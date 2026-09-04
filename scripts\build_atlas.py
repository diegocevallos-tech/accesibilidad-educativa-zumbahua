from __future__ import annotations

import gzip
import math
import textwrap
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LightSource
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "atlas_cache"
ATLAS = ROOT / "atlas"
FIGURES = ATLAS / "figures"
SOCIAL = ATLAS / "social"
DATA = ATLAS / "data"

PDF_PATH = ATLAS / "atlas-zumbahua-2026.pdf"
SCHOOL_SEED = ROOT / "data" / "manual" / "school_inventory_seed.csv"
TREND_FILE = ROOT / "reports" / "tables" / "enrollment_trend.csv"

BOUNDARY_RELATION = "R3774470"
POPULATION_2022 = 6948
POPULATION_SOURCE = "GAD Parroquial de Zumbahua, Actualización PDOT 2024-2028; dato INEC 2022"
MINEDUC_SOURCE = "Ministerio de Educación, registros administrativos 2017-2018 y 2024-2025"
OSM_SOURCE = "OpenStreetMap contributors, consulta 2026-09-04, licencia ODbL"
SRTM_SOURCE = "NASA/NGA SRTM 1 Arc-Second Global (~30 m), vía Terrain Tiles on AWS"

NAVY = "#132A3A"
INK = "#17242B"
MUTED = "#65747C"
PAPER = "#F6F2E8"
TEAL = "#167D7F"
MINT = "#8CC7B5"
OCHRE = "#E2A83B"
RED = "#C84C4C"
PURPLE = "#6F5AA8"
ROAD = "#67787E"
WHITE = "#FFFFFF"

LEVEL_COLORS = {
    "EGB": TEAL,
    "Inicial + EGB + Bachillerato": OCHRE,
    "EGB + Bachillerato": PURPLE,
}
TIME_COLORS = ["#2A9D8F", "#E9C46A", "#F4A261", "#E76F51"]
TIME_LABELS = ["≤ 30 min", "30-60 min", "60-90 min", "> 90 min"]

# Correspondencias auditables entre código AMIE y elemento OSM.
OSM_MATCHES: dict[str, tuple[str, int, str]] = {
    "05B00061": ("way", 1029346262, "alta"),
    "05B00045": ("node", 9490090885, "alta"),
    "05B00046": ("way", 1029346253, "alta"),
    "05B00058": ("way", 1029346265, "alta"),
    "05B00057": ("way", 1029346258, "alta"),
    "05B00051": ("node", 9490112923, "alta"),
    "05B00052": ("way", 1029346256, "alta"),
    "05B00060": ("way", 1029346264, "alta"),
    "05H00584": ("way", 1029346255, "alta"),
    "05H00576": ("node", 9490090871, "alta"),
    "05H00585": ("way", 1029346254, "alta"),
    "05H00586": ("node", 9490112930, "alta"),
    "05H00587": ("way", 1029346261, "alta"),
    "05H00582": ("way", 1029346257, "alta"),
    "05H00574": ("way", 361626424, "alta"),
    "05B00064": ("way", 361626426, "alta"),
    "05B00047": ("way", 1029346259, "alta"),
    "05B00050": ("node", 9490090893, "alta"),
    # OSM dice "Colegio Jatary Amancha"; el registro oficial dice Jatari Unancha.
    "05B00114": ("way", 361626422, "media"),
}


@dataclass
class AtlasData:
    boundary: gpd.GeoDataFrame
    boundary_utm: gpd.GeoDataFrame
    schools: gpd.GeoDataFrame
    schools_utm: gpd.GeoDataFrame
    roads: gpd.GeoDataFrame
    nodes: gpd.GeoDataFrame
    places: gpd.GeoDataFrame
    country: gpd.GeoDataFrame
    province: gpd.GeoDataFrame
    canton: gpd.GeoDataFrame
    trend: pd.DataFrame
    dem: np.ndarray
    dem_extent: tuple[float, float, float, float]
    hillshade: np.ndarray
    coverage: pd.DataFrame


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 17,
            "axes.titleweight": "bold",
            "axes.labelcolor": INK,
            "text.color": INK,
            "axes.edgecolor": MUTED,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "figure.facecolor": PAPER,
            "axes.facecolor": PAPER,
            "savefig.facecolor": PAPER,
        }
    )


def ensure_dirs() -> None:
    for directory in (RAW, ATLAS, FIGURES, SOCIAL, DATA):
        directory.mkdir(parents=True, exist_ok=True)


def download(url: str, destination: Path) -> Path:
    if destination.exists():
        return destination
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "zumbahua-access-atlas/0.2 (research; contact via GitHub)"},
    )
    partial = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as out:
        while block := response.read(1024 * 1024):
            out.write(block)
    partial.replace(destination)
    return destination


def fetch_osm() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, nx.MultiDiGraph, gpd.GeoDataFrame]:
    boundary_path = RAW / "zumbahua_boundary.geojson"
    features_path = RAW / "osm_education.geojson"
    places_path = RAW / "osm_places.geojson"
    graph_path = RAW / "walk.graphml"

    if boundary_path.exists():
        boundary = gpd.read_file(boundary_path)
    else:
        boundary = ox.geocode_to_gdf(BOUNDARY_RELATION, by_osmid=True)
        boundary[["display_name", "osm_type", "osm_id", "geometry"]].to_file(
            boundary_path, driver="GeoJSON"
        )

    polygon = boundary.geometry.iloc[0]
    if features_path.exists():
        education = gpd.read_file(features_path).set_index(["element", "id"])
    else:
        education = ox.features_from_polygon(
            polygon, {"amenity": ["school", "college", "kindergarten"]}
        )
        education.reset_index().to_file(features_path, driver="GeoJSON")

    if places_path.exists():
        places = gpd.read_file(places_path)
    else:
        places = ox.features_from_polygon(polygon, {"place": True}).reset_index()
        places.to_file(places_path, driver="GeoJSON")

    if graph_path.exists():
        graph = ox.load_graphml(graph_path)
    else:
        graph = ox.graph_from_polygon(polygon, network_type="walk", simplify=True, retain_all=True)
        ox.save_graphml(graph, graph_path)

    return boundary, education, graph, places


def fetch_context() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, gpd.GeoDataFrame]:
    outputs = []
    queries = ["Ecuador", "Cotopaxi, Ecuador", "Pujilí, Cotopaxi, Ecuador"]
    names = ["ecuador", "cotopaxi", "pujili"]
    for query, name in zip(queries, names, strict=True):
        path = RAW / f"{name}.geojson"
        if path.exists():
            frame = gpd.read_file(path)
        else:
            frame = ox.geocode_to_gdf(query)
            frame.to_file(path, driver="GeoJSON")
        outputs.append(frame)
    return tuple(outputs)  # type: ignore[return-value]


def srtm_tile(code: str) -> np.ndarray:
    band = code[:3]
    gz_path = RAW / f"{code}.hgt.gz"
    url = f"https://s3.amazonaws.com/elevation-tiles-prod/skadi/{band}/{code}.hgt.gz"
    download(url, gz_path)
    with gzip.open(gz_path, "rb") as stream:
        values = np.frombuffer(stream.read(), dtype=">i2")
    size = int(math.sqrt(values.size))
    if size * size != values.size:
        raise ValueError(f"Tesela SRTM inválida: {code}")
    return values.reshape((size, size)).astype(float)


def build_dem(bounds: tuple[float, float, float, float]) -> tuple[np.ndarray, tuple[float, ...]]:
    west, south, east, north = bounds
    tiles = {"S01W079": srtm_tile("S01W079"), "S02W079": srtm_tile("S02W079")}
    width = 520
    height = max(420, int(width * (north - south) / (east - west)))
    lons = np.linspace(west, east, width)
    lats = np.linspace(north, south, height)
    grid_lon, grid_lat = np.meshgrid(lons, lats)
    dem = np.empty_like(grid_lon)
    for code, array in tiles.items():
        tile_north = 0.0 if code.startswith("S01") else -1.0
        tile_south = tile_north - 1.0
        mask = (grid_lat <= tile_north) & (grid_lat >= tile_south)
        row = np.clip(
            np.rint((tile_north - grid_lat[mask]) * (array.shape[0] - 1)), 0, array.shape[0] - 1
        ).astype(int)
        col = np.clip(
            np.rint((grid_lon[mask] + 79.0) * (array.shape[1] - 1)), 0, array.shape[1] - 1
        ).astype(int)
        dem[mask] = array[row, col]
    dem[dem <= -32000] = np.nan
    return dem, (west, east, south, north)


def sample_elevation(lon: float, lat: float, arrays: dict[str, np.ndarray]) -> float:
    code = "S01W079" if lat >= -1 else "S02W079"
    array = arrays[code]
    tile_north = 0.0 if code == "S01W079" else -1.0
    row = int(np.clip(round((tile_north - lat) * (array.shape[0] - 1)), 0, array.shape[0] - 1))
    col = int(np.clip(round((lon + 79.0) * (array.shape[1] - 1)), 0, array.shape[1] - 1))
    return float(array[row, col])


def build_schools(education: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    official = pd.read_csv(SCHOOL_SEED)
    rows: list[dict[str, object]] = []
    for record in official.to_dict("records"):
        element, osm_id, confidence = OSM_MATCHES[str(record["codigo_amie"])]
        feature = education.loc[(element, osm_id)]
        geometry = feature.geometry
        if geometry.geom_type not in {"Point", "MultiPoint"}:
            geometry = geometry.representative_point()
        initial = int(record["inicial"]) == 1
        bachelor = int(record["bachillerato"]) == 1
        if initial:
            offer = "Inicial + EGB + Bachillerato"
        elif bachelor:
            offer = "EGB + Bachillerato"
        else:
            offer = "EGB"
        rows.append(
            {
                **record,
                "osm_type": element,
                "osm_id": osm_id,
                "nombre_osm": feature.get("name", ""),
                "confianza_coordenada": confidence,
                "oferta_resumida": offer,
                "geometry": geometry,
            }
        )
    schools = gpd.GeoDataFrame(rows, crs="EPSG:4326")
    schools.drop(columns=["latitud", "longitud"], errors="ignore").assign(
        latitud=schools.geometry.y, longitud=schools.geometry.x
    ).to_file(DATA / "instituciones_educativas_2024_2025.geojson", driver="GeoJSON")
    schools.drop(columns="geometry").assign(
        latitud=schools.geometry.y, longitud=schools.geometry.x
    ).to_csv(DATA / "instituciones_educativas_2024_2025.csv", index=False)
    return schools


def prepare_network(
    graph: nx.MultiDiGraph, schools: gpd.GeoDataFrame, arrays: dict[str, np.ndarray]
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, pd.DataFrame]:
    for _node, data in graph.nodes(data=True):
        data["elevation"] = sample_elevation(float(data["x"]), float(data["y"]), arrays)
    for u, v, _, data in graph.edges(keys=True, data=True):
        length = max(float(data.get("length", 1.0)), 1.0)
        rise = graph.nodes[v]["elevation"] - graph.nodes[u]["elevation"]
        grade = rise / length
        speed = 6.0 * math.exp(-3.5 * abs(grade + 0.05))
        speed = min(6.0, max(0.6, speed))
        data["walk_min"] = length / (speed * 1000 / 60)

    nearest = ox.distance.nearest_nodes(
        graph, X=schools.geometry.x.to_numpy(), Y=schools.geometry.y.to_numpy()
    )
    schools = schools.copy()
    schools["nearest_node"] = nearest

    level_masks = {
        "egb": schools["egb"].astype(int).eq(1),
        "inicial": schools["inicial"].astype(int).eq(1),
        "bachillerato": schools["bachillerato"].astype(int).eq(1),
    }
    for level, mask in level_masks.items():
        sources = schools.loc[mask, "nearest_node"].astype(int).tolist()
        distances = nx.multi_source_dijkstra_path_length(graph, sources, weight="walk_min")
        nx.set_node_attributes(graph, distances, f"time_{level}")

    graph_utm = ox.project_graph(graph, to_crs="EPSG:32717")
    nodes, edges = ox.graph_to_gdfs(graph_utm)
    nodes = nodes.reset_index()
    edges = edges.reset_index()
    edges["pair"] = edges.apply(lambda r: f"{min(r['u'], r['v'])}-{max(r['u'], r['v'])}", axis=1)
    unique = edges.sort_values("length").drop_duplicates("pair").copy()

    coverage_rows = []
    for level in level_masks:
        attribute = f"time_{level}"
        from_u = unique["u"].map(
            lambda node_id, attribute_name=attribute: graph.nodes[int(node_id)].get(
                attribute_name, np.inf
            )
        )
        from_v = unique["v"].map(
            lambda node_id, attribute_name=attribute: graph.nodes[int(node_id)].get(
                attribute_name, np.inf
            )
        )
        values = np.minimum(from_u, from_v)
        unique[f"time_{level}"] = values
        total = unique["length"].sum()
        for threshold in (30, 60, 90):
            covered = unique.loc[values <= threshold, "length"].sum()
            coverage_rows.append(
                {
                    "nivel": level,
                    "umbral_min": threshold,
                    "red_cubierta_pct": 100 * covered / total,
                }
            )

    return nodes, unique, pd.DataFrame(coverage_rows)


def load_data() -> AtlasData:
    boundary, education, graph, places = fetch_osm()
    country, province, canton = fetch_context()
    schools = build_schools(education)
    arrays = {"S01W079": srtm_tile("S01W079"), "S02W079": srtm_tile("S02W079")}
    dem, dem_extent = build_dem(boundary.total_bounds)
    hillshade = LightSource(azdeg=315, altdeg=42).hillshade(
        np.nan_to_num(dem, nan=np.nanmedian(dem)), vert_exag=1.3, dx=30, dy=30
    )
    nodes, roads, coverage = prepare_network(graph, schools, arrays)
    boundary_utm = boundary.to_crs("EPSG:32717")
    schools_utm = schools.to_crs("EPSG:32717")
    trend = pd.read_csv(TREND_FILE)
    coverage.to_csv(DATA / "cobertura_longitud_red_preliminar.csv", index=False)
    return AtlasData(
        boundary,
        boundary_utm,
        schools,
        schools_utm,
        roads,
        nodes,
        places,
        country,
        province,
        canton,
        trend,
        dem,
        dem_extent,
        hillshade,
        coverage,
    )


def clean_axis(ax: plt.Axes) -> None:
    ax.set_axis_off()
    ax.set_facecolor(PAPER)


def page_header(fig: plt.Figure, kicker: str, title: str, subtitle: str = "") -> None:
    fig.text(0.055, 0.94, kicker.upper(), color=TEAL, fontsize=8, weight="bold")
    title_size = 24 if len(title) < 55 else 20
    fig.text(0.055, 0.885, title, color=NAVY, fontsize=title_size, weight="bold")
    if subtitle:
        fig.text(0.055, 0.84, subtitle, color=MUTED, fontsize=10)
    fig.add_artist(Rectangle((0.055, 0.825), 0.89, 0.003, color=OCHRE, transform=fig.transFigure))


def footer(fig: plt.Figure, page: int, source: str) -> None:
    source_ax = fig.add_axes([0.055, 0.012, 0.77, 0.045])
    clean_axis(source_ax)
    source_ax.text(
        0,
        0.5,
        textwrap.fill(source, width=128),
        color=MUTED,
        fontsize=6.2,
        va="center",
        clip_on=True,
        transform=source_ax.transAxes,
    )
    fig.text(
        0.945, 0.028, f"ATLAS ZUMBAHUA 2026  ·  {page:02d}", color=MUTED, fontsize=7, ha="right"
    )


def add_north_and_scale(
    ax: plt.Axes, bounds: tuple[float, float, float, float], km: int = 5
) -> None:
    xmin, ymin, xmax, ymax = bounds
    width, height = xmax - xmin, ymax - ymin
    ax.annotate(
        "N",
        xy=(xmax - width * 0.055, ymax - height * 0.06),
        xytext=(xmax - width * 0.055, ymax - height * 0.18),
        ha="center",
        va="center",
        fontsize=8,
        weight="bold",
        arrowprops={"arrowstyle": "-|>", "color": NAVY, "lw": 1.3},
    )
    x0 = xmin + width * 0.06
    y0 = ymin + height * 0.055
    ax.plot([x0, x0 + km * 1000], [y0, y0], color=NAVY, lw=2)
    ax.plot([x0, x0], [y0 - height * 0.006, y0 + height * 0.006], color=NAVY, lw=1)
    ax.plot(
        [x0 + km * 1000, x0 + km * 1000],
        [y0 - height * 0.006, y0 + height * 0.006],
        color=NAVY,
        lw=1,
    )
    ax.text(x0 + km * 500, y0 + height * 0.018, f"{km} km", ha="center", fontsize=7)


def set_map_bounds(ax: plt.Axes, boundary: gpd.GeoDataFrame, pad: float = 0.025) -> None:
    xmin, ymin, xmax, ymax = boundary.total_bounds
    dx, dy = xmax - xmin, ymax - ymin
    ax.set_xlim(xmin - dx * pad, xmax + dx * pad)
    ax.set_ylim(ymin - dy * pad, ymax + dy * pad)
    ax.set_aspect("equal")


def map_base(ax: plt.Axes, data: AtlasData, roads_alpha: float = 0.4) -> None:
    data.boundary_utm.plot(ax=ax, color="#E9E4D8", edgecolor=NAVY, linewidth=1.2, zorder=1)
    data.roads.plot(ax=ax, color=ROAD, linewidth=0.35, alpha=roads_alpha, zorder=2)
    set_map_bounds(ax, data.boundary_utm)
    clean_axis(ax)


def plot_school_points(ax: plt.Axes, schools: gpd.GeoDataFrame, labels: bool = False) -> None:
    for offer, group in schools.groupby("oferta_resumida"):
        sizes = 22 + 3.7 * np.sqrt(group["estudiantes_2024_2025"].astype(float))
        ax.scatter(
            group.geometry.x,
            group.geometry.y,
            s=sizes,
            c=LEVEL_COLORS[offer],
            edgecolor=WHITE,
            linewidth=0.8,
            alpha=0.95,
            zorder=5,
            label=offer,
        )
    if labels:
        label_specs = {
            "05B00114": ("Jatari Unancha", (12, 18)),
            "05H00574": ("Cacique Tumbala", (-74, -17)),
            "05B00064": ("Don Bosco", (16, -26)),
            "05B00047": ("24 de Octubre", (8, 9)),
            "05B00050": ("Saraugsha", (8, -15)),
        }
        selected = schools[schools["codigo_amie"].isin(label_specs)]
        for _, row in selected.iterrows():
            short, offset = label_specs[str(row["codigo_amie"])]
            ax.annotate(
                short,
                (row.geometry.x, row.geometry.y),
                xytext=offset,
                textcoords="offset points",
                fontsize=6.2,
                color=INK,
                zorder=7,
                bbox={
                    "boxstyle": "round,pad=0.15",
                    "facecolor": PAPER,
                    "edgecolor": "none",
                    "alpha": 0.82,
                },
                arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.45},
            )


def time_category(values: pd.Series) -> np.ndarray:
    return np.digitize(values.to_numpy(dtype=float), bins=[30, 60, 90], right=True)


def access_map(ax: plt.Axes, data: AtlasData, level: str, title: str) -> None:
    data.boundary_utm.plot(ax=ax, color="#EEE9DE", edgecolor=NAVY, linewidth=0.9, zorder=0)
    categories = time_category(data.roads[f"time_{level}"])
    for category, color in enumerate(TIME_COLORS):
        subset = data.roads.loc[categories == category]
        subset.plot(ax=ax, color=color, linewidth=0.7, alpha=0.92, zorder=2)
    schools = data.schools_utm[data.schools_utm[level].astype(int).eq(1)]
    ax.scatter(
        schools.geometry.x,
        schools.geometry.y,
        marker="^",
        s=36,
        facecolor=NAVY,
        edgecolor=WHITE,
        linewidth=0.7,
        zorder=6,
    )
    set_map_bounds(ax, data.boundary_utm)
    clean_axis(ax)
    ax.set_title(title, loc="left", color=NAVY, pad=8)


def save_page(fig: plt.Figure, pdf: PdfPages, name: str) -> None:
    pdf.savefig(fig, dpi=220, bbox_inches=None)
    fig.savefig(FIGURES / f"{name}.png", dpi=220, bbox_inches="tight", facecolor=PAPER)
    plt.close(fig)


def cover_page(data: AtlasData, pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27), facecolor=NAVY)
    ax = fig.add_axes([0.53, 0.06, 0.45, 0.88])
    ax.set_facecolor(NAVY)
    data.boundary_utm.plot(ax=ax, color="#1F4355", edgecolor=MINT, linewidth=1.6)
    data.roads.plot(ax=ax, color=MINT, linewidth=0.35, alpha=0.38)
    data.schools_utm.plot(ax=ax, color=OCHRE, markersize=18, edgecolor=WHITE, linewidth=0.4)
    set_map_bounds(ax, data.boundary_utm, pad=0.06)
    clean_axis(ax)
    ax.set_facecolor(NAVY)

    fig.text(0.065, 0.82, "ATLAS PRELIMINAR · 2026", color=MINT, fontsize=10, weight="bold")
    fig.text(
        0.065,
        0.68,
        "Accesibilidad\neducativa en\nZumbahua",
        color=WHITE,
        fontsize=36,
        weight="bold",
        linespacing=0.95,
    )
    fig.text(
        0.065,
        0.48,
        (
            "Reconstrucción cartográfica, cambio de la oferta\n"
            "y accesibilidad potencial por red peatonal"
        ),
        color="#D7E5E5",
        fontsize=12,
        linespacing=1.35,
    )
    fig.text(
        0.065, 0.23, "Diego Santiago Cevallos Valencia", color=WHITE, fontsize=11, weight="bold"
    )
    fig.text(0.065, 0.19, "Estudio reproducible desde gabinete", color=MINT, fontsize=9)
    fig.text(
        0.065,
        0.07,
        "Versión 0.2 · Resultados espaciales preliminares sujetos a validación censal y de campo",
        color="#AFC3C8",
        fontsize=7.5,
    )
    pdf.savefig(fig, dpi=220, facecolor=NAVY)
    fig.savefig(FIGURES / "00_portada.png", dpi=220, facecolor=NAVY)
    plt.close(fig)


def context_page(data: AtlasData, pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    page_header(
        fig,
        "01 · Territorio",
        "Una parroquia rural andina extensa y dispersa",
        "La ubicación de las escuelas debe interpretarse junto con la red de caminos y el relieve.",
    )
    ax = fig.add_axes([0.055, 0.10, 0.62, 0.68])
    map_base(ax, data, roads_alpha=0.55)
    plot_school_points(ax, data.schools_utm)
    add_north_and_scale(ax, data.boundary_utm.total_bounds, km=5)

    inset = fig.add_axes([0.70, 0.48, 0.25, 0.28])
    data.country.plot(ax=inset, color="#DFE7E5", edgecolor=NAVY, linewidth=0.6)
    data.province.plot(ax=inset, color=OCHRE, edgecolor=NAVY, linewidth=0.5)
    centroid = data.boundary.geometry.iloc[0].centroid
    inset.scatter([centroid.x], [centroid.y], s=28, color=RED, zorder=5)
    inset.text(centroid.x + 0.25, centroid.y, "Zumbahua", fontsize=7, va="center", weight="bold")
    inset.set_title("Ubicación en Ecuador", fontsize=10, loc="left")
    clean_axis(inset)

    stats_ax = fig.add_axes([0.70, 0.12, 0.25, 0.30])
    clean_axis(stats_ax)
    stats = [
        ("6.948", "habitantes censados en 2022"),
        ("19", "instituciones registradas en 2024-2025"),
        ("2.302", "estudiantes registrados en 2024-2025"),
        ("~600 km", "de red OSM caminable modelada"),
    ]
    y = 0.92
    for value, label in stats:
        stats_ax.text(
            0.0, y, value, fontsize=19, color=NAVY, weight="bold", transform=stats_ax.transAxes
        )
        stats_ax.text(0.0, y - 0.12, label, fontsize=8.3, color=MUTED, transform=stats_ax.transAxes)
        y -= 0.24
    footer(fig, 2, f"Fuentes: {POPULATION_SOURCE}; {MINEDUC_SOURCE}; {OSM_SOURCE}.")
    save_page(fig, pdf, "01_contexto")


def terrain_page(data: AtlasData, pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    page_header(
        fig,
        "02 · Relieve",
        "La pendiente transforma distancia en esfuerzo",
        (
            "El modelo peatonal ajusta la velocidad por pendiente; "
            "un radio plano no representa el viaje andino."
        ),
    )
    ax = fig.add_axes([0.055, 0.10, 0.70, 0.69])
    west, east, south, north = data.dem_extent
    im = ax.imshow(
        data.dem,
        extent=(west, east, south, north),
        cmap="terrain",
        origin="upper",
        alpha=0.84,
        zorder=0,
    )
    ax.imshow(
        data.hillshade,
        extent=(west, east, south, north),
        cmap="gray",
        origin="upper",
        alpha=0.24,
        zorder=1,
    )
    data.boundary.boundary.plot(ax=ax, color=NAVY, linewidth=1.1, zorder=4)
    roads_wgs = data.roads.to_crs("EPSG:4326")
    roads_wgs.plot(ax=ax, color=WHITE, linewidth=0.32, alpha=0.55, zorder=2)
    data.schools.plot(ax=ax, color=RED, markersize=18, edgecolor=WHITE, linewidth=0.45, zorder=5)
    ax.set_xlim(west, east)
    ax.set_ylim(south, north)
    ax.set_aspect("equal")
    clean_axis(ax)
    cbar = fig.colorbar(im, ax=ax, fraction=0.027, pad=0.015)
    cbar.ax.set_title("m s. n. m.", fontsize=7, color=INK, pad=5)
    cbar.ax.tick_params(labelsize=7)

    note = fig.add_axes([0.84, 0.17, 0.11, 0.52])
    clean_axis(note)
    note.text(0, 0.98, "LECTURA", fontsize=9, color=TEAL, weight="bold", transform=note.transAxes)
    note.text(
        0,
        0.86,
        textwrap.fill(
            (
                "Las escuelas no se distribuyen sobre una superficie homogénea. "
                "Los desniveles penalizan rutas y pueden aislar sectores que "
                "parecen cercanos en línea recta."
            ),
            width=22,
        ),
        fontsize=8.2,
        color=INK,
        va="top",
        wrap=True,
        linespacing=1.35,
        transform=note.transAxes,
    )
    footer(fig, 3, f"Fuentes: {SRTM_SOURCE}; {OSM_SOURCE}.")
    save_page(fig, pdf, "02_relieve")


def supply_page(data: AtlasData, pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    page_header(
        fig,
        "03 · Oferta educativa",
        "Diecinueve instituciones, tres geografías educativas",
        "El tamaño representa matrícula; el color identifica los niveles ofertados.",
    )
    ax = fig.add_axes([0.055, 0.10, 0.70, 0.69])
    map_base(ax, data, roads_alpha=0.42)
    plot_school_points(ax, data.schools_utm, labels=True)
    add_north_and_scale(ax, data.boundary_utm.total_bounds, km=5)
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=color,
            markeredgecolor=WHITE,
            markersize=8,
            label=label,
        )
        for label, color in LEVEL_COLORS.items()
    ]
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=7.5)

    side = fig.add_axes([0.79, 0.12, 0.16, 0.60])
    clean_axis(side)
    counts = data.schools.groupby("oferta_resumida").size()
    side.text(0, 1.0, "OFERTA 2024-2025", color=TEAL, fontsize=9, weight="bold", va="top")
    side.text(0, 0.86, f"{int(counts.get('EGB', 0))}", fontsize=25, weight="bold", color=NAVY)
    side.text(0, 0.79, "solo EGB", fontsize=8.5, color=MUTED)
    side.text(
        0,
        0.65,
        f"{int(counts.get('Inicial + EGB + Bachillerato', 0))}",
        fontsize=25,
        weight="bold",
        color=OCHRE,
    )
    side.text(0, 0.58, "Inicial + EGB + Bach.", fontsize=8.5, color=MUTED)
    side.text(
        0,
        0.44,
        f"{int(counts.get('EGB + Bachillerato', 0))}",
        fontsize=25,
        weight="bold",
        color=PURPLE,
    )
    side.text(0, 0.37, "EGB + Bachillerato", fontsize=8.5, color=MUTED)
    side.text(
        0,
        0.19,
        (
            "La disponibilidad de bachillerato e inicial es mucho más "
            "concentrada que la oferta de EGB."
        ),
        fontsize=8.5,
        color=INK,
        va="top",
        wrap=True,
        linespacing=1.35,
    )
    footer(fig, 4, f"Fuentes: {MINEDUC_SOURCE}; coordenadas reconstruidas con {OSM_SOURCE}.")
    save_page(fig, pdf, "03_oferta_educativa")


def history_page(data: AtlasData, pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    page_header(
        fig,
        "04 · Cambio temporal",
        "La matrícula registrada cae más rápido que la infraestructura escolar",
        "La discontinuidad de 2022-2023 obliga a interpretar la serie con cautela.",
    )
    trend = data.trend.copy()
    years = np.arange(len(trend))
    ax = fig.add_axes([0.07, 0.18, 0.63, 0.58])
    ax.plot(years, trend["estudiantes"], color=TEAL, lw=2.5, marker="o", ms=4)
    ax.fill_between(years, trend["estudiantes"], color=MINT, alpha=0.18)
    ax.set_ylabel("Estudiantes registrados")
    ax.set_xticks(years[::2])
    ax.set_xticklabels(
        [str(x).split()[0] for x in trend["periodo"].iloc[::2]], rotation=35, ha="right"
    )
    ax.grid(axis="y", color="#D3CEC3", lw=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    for period in ("2017-2018 Inicio", "2024-2025 Inicio"):
        row = trend.loc[trend["periodo"] == period].iloc[0]
        idx = trend.index[trend["periodo"] == period][0]
        ax.annotate(
            f"{int(round(row['estudiantes'])):,}".replace(",", "."),
            (idx, row["estudiantes"]),
            xytext=(0, 12),
            textcoords="offset points",
            ha="center",
            color=NAVY,
            weight="bold",
        )

    side = fig.add_axes([0.75, 0.18, 0.20, 0.58])
    clean_axis(side)
    side.text(0, 0.95, "2017-2018 → 2024-2025", color=TEAL, fontsize=9, weight="bold")
    side.text(0, 0.77, "-51,2 %", color=RED, fontsize=28, weight="bold")
    side.text(0, 0.70, "matrícula registrada", color=MUTED, fontsize=9)
    side.text(0, 0.54, "-5,0 %", color=NAVY, fontsize=22, weight="bold")
    side.text(0, 0.48, "instituciones", color=MUTED, fontsize=9)
    side.text(0, 0.34, "-8,8 %", color=NAVY, fontsize=22, weight="bold")
    side.text(0, 0.28, "docentes", color=MUTED, fontsize=9)
    side.text(
        0,
        0.11,
        (
            "No equivale todavía a deserción: deben revisarse migración, cobertura, "
            "cierres, fusiones y cambios del registro."
        ),
        color=INK,
        fontsize=8.2,
        va="top",
        wrap=True,
    )
    footer(fig, 5, f"Fuente: {MINEDUC_SOURCE}. Cálculos propios; valores preliminares.")
    save_page(fig, pdf, "04_cambio_temporal")


def egb_page(data: AtlasData, pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    page_header(
        fig,
        "05 · Accesibilidad potencial",
        "EGB presenta la cobertura espacial más extendida",
        (
            "Tiempo mínimo por la red caminable, con velocidad ajustada por pendiente; "
            "triángulos = instituciones."
        ),
    )
    ax = fig.add_axes([0.055, 0.10, 0.72, 0.69])
    access_map(ax, data, "egb", "")
    add_north_and_scale(ax, data.boundary_utm.total_bounds, km=5)
    handles = [
        Line2D([0], [0], color=color, lw=3, label=label)
        for color, label in zip(TIME_COLORS, TIME_LABELS, strict=True)
    ]
    handles.append(
        Line2D(
            [0],
            [0],
            marker="^",
            color="none",
            markerfacecolor=NAVY,
            markersize=7,
            label="Institución con EGB",
        )
    )
    ax.legend(handles=handles, loc="lower right", frameon=False, fontsize=7.5)
    side = fig.add_axes([0.81, 0.15, 0.14, 0.54])
    clean_axis(side)
    cov = data.coverage[data.coverage["nivel"] == "egb"].set_index("umbral_min")
    side.text(0, 0.98, "RED CUBIERTA*", color=TEAL, fontsize=9, weight="bold")
    y = 0.82
    for threshold in (30, 60, 90):
        value = cov.loc[threshold, "red_cubierta_pct"]
        side.text(0, y, f"{value:.0f} %", fontsize=22, color=NAVY, weight="bold")
        side.text(0, y - 0.07, f"en ≤ {threshold} minutos", fontsize=8, color=MUTED)
        y -= 0.20
    side.text(
        0,
        0.17,
        (
            "*Proporción de longitud vial modelada, no de población. "
            "Será sustituida por cobertura censal ponderada."
        ),
        fontsize=7.7,
        color=INK,
        va="top",
        wrap=True,
    )
    footer(
        fig,
        6,
        f"Fuentes: {OSM_SOURCE}; {SRTM_SOURCE}; oferta: MINEDUC 2024-2025. Modelo preliminar.",
    )
    save_page(fig, pdf, "05_accesibilidad_egb")


def level_comparison_page(data: AtlasData, pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    page_header(
        fig,
        "06 · Brecha por nivel",
        "Inicial y bachillerato dependen de pocos destinos",
        (
            "La misma red produce geografías educativas diferentes según "
            "el nivel que una persona necesita."
        ),
    )
    ax1 = fig.add_axes([0.055, 0.16, 0.43, 0.60])
    ax2 = fig.add_axes([0.515, 0.16, 0.43, 0.60])
    access_map(ax1, data, "inicial", "Educación inicial")
    access_map(ax2, data, "bachillerato", "Bachillerato")
    handles = [
        Line2D([0], [0], color=color, lw=3, label=label)
        for color, label in zip(TIME_COLORS, TIME_LABELS, strict=True)
    ]
    fig.legend(
        handles=handles,
        loc="lower center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 0.085),
        fontsize=8,
    )
    footer(
        fig,
        7,
        f"Fuentes: {OSM_SOURCE}; {SRTM_SOURCE}; oferta: MINEDUC 2024-2025. Modelo preliminar.",
    )
    save_page(fig, pdf, "06_comparacion_niveles")


def evidence_page(data: AtlasData, pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    page_header(
        fig,
        "07 · Evidencia y próximos pasos",
        "Un atlas honesto separa resultados de hipótesis",
        (
            "La cartografía ya permite localizar el problema, pero la inferencia social "
            "requiere población censal y validación."
        ),
    )
    ax = fig.add_axes([0.055, 0.10, 0.89, 0.69])
    clean_axis(ax)
    columns = [
        (
            "CONFIRMADO",
            TEAL,
            [
                "19 instituciones en el registro 2024-2025.",
                "18 coordenadas con coincidencia OSM alta.",
                "1 coordenada con coincidencia media.",
                "2.302 estudiantes y 206 docentes registrados.",
                "6.948 habitantes reportados para 2022.",
            ],
        ),
        (
            "MODELO PRELIMINAR",
            OCHRE,
            [
                "Red caminable extraída de OpenStreetMap.",
                "Velocidad ajustada por pendiente SRTM.",
                "Tiempos al destino más cercano por nivel.",
                "Cobertura expresada sobre longitud de red.",
                "Escenario potencial, no viajes observados.",
            ],
        ),
        (
            "FALTA PARA PUBLICAR RESULTADOS",
            RED,
            [
                "Sectores y población por edad del Censo 2022.",
                "Auditoría manual de caminos y coordenadas.",
                "Capacidad escolar y competencia por oferta.",
                "Sensibilidad de velocidades y exclusiones.",
                "Validación comunitaria o de campo, si es posible.",
            ],
        ),
    ]
    for i, (title, color, items) in enumerate(columns):
        x = 0.01 + i * 0.335
        box = FancyBboxPatch(
            (x, 0.12),
            0.30,
            0.76,
            boxstyle="round,pad=0.018,rounding_size=0.015",
            facecolor=WHITE,
            edgecolor="#D7D2C8",
            linewidth=0.8,
            transform=ax.transAxes,
        )
        ax.add_patch(box)
        ax.add_patch(Rectangle((x, 0.82), 0.30, 0.06, color=color, transform=ax.transAxes))
        ax.text(
            x + 0.02,
            0.85,
            title,
            color=WHITE,
            fontsize=8.3,
            weight="bold",
            va="center",
            transform=ax.transAxes,
        )
        y = 0.74
        for item in items:
            ax.text(x + 0.025, y, "•", color=color, fontsize=12, va="top", transform=ax.transAxes)
            ax.text(
                x + 0.055,
                y,
                textwrap.fill(item, 32),
                color=INK,
                fontsize=8.7,
                va="top",
                linespacing=1.35,
                transform=ax.transAxes,
            )
            y -= 0.125
    footer(
        fig,
        8,
        (
            "Síntesis metodológica del proyecto. Los mapas de accesibilidad "
            "no representan viajes observados."
        ),
    )
    save_page(fig, pdf, "07_evidencia_y_limites")


def social_card_map(data: AtlasData, level: str, title: str, subtitle: str, filename: str) -> None:
    fig = plt.figure(figsize=(8, 10), facecolor=PAPER)
    fig.text(0.07, 0.94, "ZUMBAHUA · ATLAS 2026", color=TEAL, fontsize=10, weight="bold")
    fig.text(0.07, 0.875, title, color=NAVY, fontsize=23, weight="bold")
    fig.text(0.07, 0.825, subtitle, color=MUTED, fontsize=9)
    ax = fig.add_axes([0.07, 0.17, 0.86, 0.60])
    access_map(ax, data, level, "")
    handles = [
        Line2D([0], [0], color=color, lw=3, label=label)
        for color, label in zip(TIME_COLORS, TIME_LABELS, strict=True)
    ]
    ax.legend(handles=handles, loc="lower center", ncol=2, frameon=False, fontsize=8)
    fig.text(
        0.07,
        0.075,
        "Tiempo potencial por red caminable · pendiente SRTM · resultados preliminares",
        color=INK,
        fontsize=8,
    )
    fig.text(
        0.07,
        0.045,
        "Fuentes: MINEDUC 2024-2025, OpenStreetMap y NASA/NGA SRTM.",
        color=MUTED,
        fontsize=7,
    )
    fig.savefig(SOCIAL / filename, dpi=135, facecolor=PAPER)
    plt.close(fig)


def social_history(data: AtlasData) -> None:
    fig = plt.figure(figsize=(8, 10), facecolor=PAPER)
    fig.text(0.07, 0.94, "ZUMBAHUA · ATLAS 2026", color=TEAL, fontsize=10, weight="bold")
    fig.text(
        0.07,
        0.87,
        "La matrícula registrada\nse redujo 51,2 %",
        color=NAVY,
        fontsize=25,
        weight="bold",
    )
    fig.text(0.07, 0.79, "Comparación preliminar 2017-2018 / 2024-2025", color=MUTED, fontsize=9)
    ax = fig.add_axes([0.10, 0.29, 0.80, 0.43])
    t = data.trend
    x = np.arange(len(t))
    ax.plot(x, t["estudiantes"], color=TEAL, lw=3, marker="o", ms=4)
    ax.fill_between(x, t["estudiantes"], color=MINT, alpha=0.18)
    ax.set_xticks(x[::3])
    ax.set_xticklabels([str(v).split()[0] for v in t["periodo"].iloc[::3]], rotation=30, ha="right")
    ax.set_ylabel("Estudiantes")
    ax.grid(axis="y", color="#D3CEC3", lw=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.07, 0.17, "Esto no demuestra deserción.", color=RED, fontsize=13, weight="bold")
    fig.text(
        0.07,
        0.105,
        (
            "Se deben contrastar migración, cambios administrativos, cierres, "
            "fusiones y comparabilidad del registro."
        ),
        color=INK,
        fontsize=9,
        wrap=True,
    )
    fig.text(0.07, 0.045, f"Fuente: {MINEDUC_SOURCE}. Cálculos propios.", color=MUTED, fontsize=7)
    fig.savefig(SOCIAL / "04_cambio_matricula.png", dpi=135, facecolor=PAPER)
    plt.close(fig)


def social_supply(data: AtlasData) -> None:
    fig = plt.figure(figsize=(8, 10), facecolor=PAPER)
    fig.text(0.07, 0.94, "ZUMBAHUA · ATLAS 2026", color=TEAL, fontsize=10, weight="bold")
    fig.text(
        0.07,
        0.87,
        "No todas las escuelas\nofrecen lo mismo",
        color=NAVY,
        fontsize=25,
        weight="bold",
    )
    ax = fig.add_axes([0.07, 0.19, 0.86, 0.57])
    map_base(ax, data, roads_alpha=0.35)
    plot_school_points(ax, data.schools_utm)
    handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=color,
            markersize=8,
            label=label,
        )
        for label, color in LEVEL_COLORS.items()
    ]
    ax.legend(handles=handles, loc="lower center", frameon=False, fontsize=7.5)
    fig.text(
        0.07,
        0.10,
        "19 instituciones registradas · tamaño del círculo = matrícula",
        color=INK,
        fontsize=9,
        weight="bold",
    )
    fig.text(
        0.07,
        0.045,
        "Fuentes: MINEDUC 2024-2025 y OpenStreetMap. Coordenadas preliminares.",
        color=MUTED,
        fontsize=7,
    )
    fig.savefig(SOCIAL / "01_oferta_educativa.png", dpi=135, facecolor=PAPER)
    plt.close(fig)


def build_atlas() -> None:
    ensure_dirs()
    configure_style()
    ox.settings.use_cache = True
    ox.settings.requests_timeout = 180
    data = load_data()
    with PdfPages(
        PDF_PATH,
        metadata={
            "Title": "Atlas preliminar de accesibilidad educativa en Zumbahua 2026",
            "Author": "Diego Santiago Cevallos Valencia",
            "Subject": "Accesibilidad educativa, territorio y reconstrucción cartográfica",
            "Keywords": "Zumbahua, educación, accesibilidad, SIG, Ecuador",
        },
    ) as pdf:
        cover_page(data, pdf)
        context_page(data, pdf)
        terrain_page(data, pdf)
        supply_page(data, pdf)
        history_page(data, pdf)
        egb_page(data, pdf)
        level_comparison_page(data, pdf)
        evidence_page(data, pdf)

    social_supply(data)
    social_card_map(
        data,
        "egb",
        "Acceso potencial a EGB",
        "La oferta más extendida, pero con tramos periféricos todavía alejados.",
        "02_accesibilidad_egb.png",
    )
    social_card_map(
        data,
        "inicial",
        "Acceso potencial a inicial",
        "Pocos destinos producen una geografía de acceso más concentrada.",
        "03_accesibilidad_inicial.png",
    )
    social_card_map(
        data,
        "bachillerato",
        "Acceso potencial a bachillerato",
        "El nivel requerido importa tanto como la distancia a una escuela.",
        "05_accesibilidad_bachillerato.png",
    )
    social_history(data)
    print(PDF_PATH)


if __name__ == "__main__":
    build_atlas()
