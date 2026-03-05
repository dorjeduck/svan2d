"""Periodic table element data, category colors, and grid positioning."""

from dataclasses import dataclass

from svan2d.core.point2d import Point2D


@dataclass(frozen=True)
class ElementData:
    atomic_number: int
    symbol: str
    name: str
    category: str
    group: int  # column 1-18
    period: int  # row 1-7, 8=lanthanides, 9=actinides
    discovery_year: int  # approximate; negative = BCE


# 10 categories with distinguishable hex colors
CATEGORY_COLORS: dict[str, str] = {
    "alkali_metal": "#FF6B35",
    "alkaline_earth": "#FDCA40",
    "transition_metal": "#4ECDC4",
    "post_transition_metal": "#45B7D1",
    "metalloid": "#96CEB4",
    "reactive_nonmetal": "#7BC67E",
    "halogen": "#DDA0DD",
    "noble_gas": "#A78BFA",
    "lanthanide": "#F9A8D4",
    "actinide": "#FCA5A5",
}


# Grid layout constants (internal coordinate system, arbitrary units)
COLS = 18
ROWS = 10
CELL_SIZE = 72
GAP = 4
PADDING = 100


def table_size() -> tuple[float, float]:
    """Compute scene dimensions from grid layout constants."""
    step = CELL_SIZE + GAP
    total_w = COLS * step - GAP + 2 * PADDING
    total_h = ROWS * step - GAP + 2 * PADDING
    return total_w, total_h


def _table_offset() -> tuple[float, float]:
    """Compute offset to center the table at origin."""
    step = CELL_SIZE + GAP
    total_w = COLS * step - GAP
    total_h = ROWS * step - GAP
    return -total_w / 2 + CELL_SIZE / 2, -total_h / 2 + CELL_SIZE / 2


def grid_position(element: ElementData) -> Point2D:
    """Compute position from group/period, centered at origin."""
    ox, oy = _table_offset()
    col = element.group - 1
    if element.period <= 7:
        row = element.period - 1
    else:
        row = element.period  # 8=lanthanides, 9=actinides (blank row 7 gap)

    step = CELL_SIZE + GAP
    x = ox + col * step
    y = oy + row * step
    return Point2D(x, y)


# fmt: off
ELEMENTS: list[ElementData] = [
    # Row 1
    ElementData(1, "H", "Hydrogen", "reactive_nonmetal", 1, 1, 1766),
    ElementData(2, "He", "Helium", "noble_gas", 18, 1, 1868),
    # Row 2
    ElementData(3, "Li", "Lithium", "alkali_metal", 1, 2, 1817),
    ElementData(4, "Be", "Beryllium", "alkaline_earth", 2, 2, 1798),
    ElementData(5, "B", "Boron", "metalloid", 13, 2, 1808),
    ElementData(6, "C", "Carbon", "reactive_nonmetal", 14, 2, -3750),
    ElementData(7, "N", "Nitrogen", "reactive_nonmetal", 15, 2, 1772),
    ElementData(8, "O", "Oxygen", "reactive_nonmetal", 16, 2, 1774),
    ElementData(9, "F", "Fluorine", "halogen", 17, 2, 1886),
    ElementData(10, "Ne", "Neon", "noble_gas", 18, 2, 1898),
    # Row 3
    ElementData(11, "Na", "Sodium", "alkali_metal", 1, 3, 1807),
    ElementData(12, "Mg", "Magnesium", "alkaline_earth", 2, 3, 1808),
    ElementData(13, "Al", "Aluminium", "post_transition_metal", 13, 3, 1825),
    ElementData(14, "Si", "Silicon", "metalloid", 14, 3, 1824),
    ElementData(15, "P", "Phosphorus", "reactive_nonmetal", 15, 3, 1669),
    ElementData(16, "S", "Sulfur", "reactive_nonmetal", 16, 3, -2000),
    ElementData(17, "Cl", "Chlorine", "halogen", 17, 3, 1774),
    ElementData(18, "Ar", "Argon", "noble_gas", 18, 3, 1894),
    # Row 4
    ElementData(19, "K", "Potassium", "alkali_metal", 1, 4, 1807),
    ElementData(20, "Ca", "Calcium", "alkaline_earth", 2, 4, 1808),
    ElementData(21, "Sc", "Scandium", "transition_metal", 3, 4, 1879),
    ElementData(22, "Ti", "Titanium", "transition_metal", 4, 4, 1791),
    ElementData(23, "V", "Vanadium", "transition_metal", 5, 4, 1801),
    ElementData(24, "Cr", "Chromium", "transition_metal", 6, 4, 1797),
    ElementData(25, "Mn", "Manganese", "transition_metal", 7, 4, 1774),
    ElementData(26, "Fe", "Iron", "transition_metal", 8, 4, -5000),
    ElementData(27, "Co", "Cobalt", "transition_metal", 9, 4, 1735),
    ElementData(28, "Ni", "Nickel", "transition_metal", 10, 4, 1751),
    ElementData(29, "Cu", "Copper", "transition_metal", 11, 4, -9000),
    ElementData(30, "Zn", "Zinc", "transition_metal", 12, 4, 1746),
    ElementData(31, "Ga", "Gallium", "post_transition_metal", 13, 4, 1875),
    ElementData(32, "Ge", "Germanium", "metalloid", 14, 4, 1886),
    ElementData(33, "As", "Arsenic", "metalloid", 15, 4, 1250),
    ElementData(34, "Se", "Selenium", "reactive_nonmetal", 16, 4, 1817),
    ElementData(35, "Br", "Bromine", "halogen", 17, 4, 1826),
    ElementData(36, "Kr", "Krypton", "noble_gas", 18, 4, 1898),
    # Row 5
    ElementData(37, "Rb", "Rubidium", "alkali_metal", 1, 5, 1861),
    ElementData(38, "Sr", "Strontium", "alkaline_earth", 2, 5, 1790),
    ElementData(39, "Y", "Yttrium", "transition_metal", 3, 5, 1794),
    ElementData(40, "Zr", "Zirconium", "transition_metal", 4, 5, 1789),
    ElementData(41, "Nb", "Niobium", "transition_metal", 5, 5, 1801),
    ElementData(42, "Mo", "Molybdenum", "transition_metal", 6, 5, 1781),
    ElementData(43, "Tc", "Technetium", "transition_metal", 7, 5, 1937),
    ElementData(44, "Ru", "Ruthenium", "transition_metal", 8, 5, 1844),
    ElementData(45, "Rh", "Rhodium", "transition_metal", 9, 5, 1803),
    ElementData(46, "Pd", "Palladium", "transition_metal", 10, 5, 1803),
    ElementData(47, "Ag", "Silver", "transition_metal", 11, 5, -5000),
    ElementData(48, "Cd", "Cadmium", "transition_metal", 12, 5, 1817),
    ElementData(49, "In", "Indium", "post_transition_metal", 13, 5, 1863),
    ElementData(50, "Sn", "Tin", "post_transition_metal", 14, 5, -3500),
    ElementData(51, "Sb", "Antimony", "metalloid", 15, 5, -3000),
    ElementData(52, "Te", "Tellurium", "metalloid", 16, 5, 1783),
    ElementData(53, "I", "Iodine", "halogen", 17, 5, 1811),
    ElementData(54, "Xe", "Xenon", "noble_gas", 18, 5, 1898),
    # Row 6 (main table, no La — it's in row 8)
    ElementData(55, "Cs", "Caesium", "alkali_metal", 1, 6, 1860),
    ElementData(56, "Ba", "Barium", "alkaline_earth", 2, 6, 1808),
    ElementData(72, "Hf", "Hafnium", "transition_metal", 4, 6, 1923),
    ElementData(73, "Ta", "Tantalum", "transition_metal", 5, 6, 1802),
    ElementData(74, "W", "Tungsten", "transition_metal", 6, 6, 1783),
    ElementData(75, "Re", "Rhenium", "transition_metal", 7, 6, 1925),
    ElementData(76, "Os", "Osmium", "transition_metal", 8, 6, 1803),
    ElementData(77, "Ir", "Iridium", "transition_metal", 9, 6, 1803),
    ElementData(78, "Pt", "Platinum", "transition_metal", 10, 6, 1735),
    ElementData(79, "Au", "Gold", "transition_metal", 11, 6, -6000),
    ElementData(80, "Hg", "Mercury", "transition_metal", 12, 6, -1500),
    ElementData(81, "Tl", "Thallium", "post_transition_metal", 13, 6, 1861),
    ElementData(82, "Pb", "Lead", "post_transition_metal", 14, 6, -7000),
    ElementData(83, "Bi", "Bismuth", "post_transition_metal", 15, 6, 1753),
    ElementData(84, "Po", "Polonium", "post_transition_metal", 16, 6, 1898),
    ElementData(85, "At", "Astatine", "halogen", 17, 6, 1940),
    ElementData(86, "Rn", "Radon", "noble_gas", 18, 6, 1900),
    # Row 7 (main table, no Ac — it's in row 9)
    ElementData(87, "Fr", "Francium", "alkali_metal", 1, 7, 1939),
    ElementData(88, "Ra", "Radium", "alkaline_earth", 2, 7, 1898),
    ElementData(104, "Rf", "Rutherfordium", "transition_metal", 4, 7, 1969),
    ElementData(105, "Db", "Dubnium", "transition_metal", 5, 7, 1970),
    ElementData(106, "Sg", "Seaborgium", "transition_metal", 6, 7, 1974),
    ElementData(107, "Bh", "Bohrium", "transition_metal", 7, 7, 1981),
    ElementData(108, "Hs", "Hassium", "transition_metal", 8, 7, 1984),
    ElementData(109, "Mt", "Meitnerium", "transition_metal", 9, 7, 1982),
    ElementData(110, "Ds", "Darmstadtium", "transition_metal", 10, 7, 1994),
    ElementData(111, "Rg", "Roentgenium", "transition_metal", 11, 7, 1994),
    ElementData(112, "Cn", "Copernicium", "transition_metal", 12, 7, 1996),
    ElementData(113, "Nh", "Nihonium", "post_transition_metal", 13, 7, 2003),
    ElementData(114, "Fl", "Flerovium", "post_transition_metal", 14, 7, 1999),
    ElementData(115, "Mc", "Moscovium", "post_transition_metal", 15, 7, 2003),
    ElementData(116, "Lv", "Livermorium", "post_transition_metal", 16, 7, 2000),
    ElementData(117, "Ts", "Tennessine", "halogen", 17, 7, 2010),
    ElementData(118, "Og", "Oganesson", "noble_gas", 18, 7, 2006),
    # Row 8 — Lanthanides (La through Lu, groups 3-17)
    ElementData(57, "La", "Lanthanum", "lanthanide", 3, 8, 1839),
    ElementData(58, "Ce", "Cerium", "lanthanide", 4, 8, 1803),
    ElementData(59, "Pr", "Praseodymium", "lanthanide", 5, 8, 1885),
    ElementData(60, "Nd", "Neodymium", "lanthanide", 6, 8, 1885),
    ElementData(61, "Pm", "Promethium", "lanthanide", 7, 8, 1945),
    ElementData(62, "Sm", "Samarium", "lanthanide", 8, 8, 1879),
    ElementData(63, "Eu", "Europium", "lanthanide", 9, 8, 1901),
    ElementData(64, "Gd", "Gadolinium", "lanthanide", 10, 8, 1880),
    ElementData(65, "Tb", "Terbium", "lanthanide", 11, 8, 1843),
    ElementData(66, "Dy", "Dysprosium", "lanthanide", 12, 8, 1886),
    ElementData(67, "Ho", "Holmium", "lanthanide", 13, 8, 1878),
    ElementData(68, "Er", "Erbium", "lanthanide", 14, 8, 1843),
    ElementData(69, "Tm", "Thulium", "lanthanide", 15, 8, 1879),
    ElementData(70, "Yb", "Ytterbium", "lanthanide", 16, 8, 1878),
    ElementData(71, "Lu", "Lutetium", "lanthanide", 17, 8, 1907),
    # Row 9 — Actinides (Ac through Lr, groups 3-17)
    ElementData(89, "Ac", "Actinium", "actinide", 3, 9, 1899),
    ElementData(90, "Th", "Thorium", "actinide", 4, 9, 1829),
    ElementData(91, "Pa", "Protactinium", "actinide", 5, 9, 1913),
    ElementData(92, "U", "Uranium", "actinide", 6, 9, 1789),
    ElementData(93, "Np", "Neptunium", "actinide", 7, 9, 1940),
    ElementData(94, "Pu", "Plutonium", "actinide", 8, 9, 1940),
    ElementData(95, "Am", "Americium", "actinide", 9, 9, 1944),
    ElementData(96, "Cm", "Curium", "actinide", 10, 9, 1944),
    ElementData(97, "Bk", "Berkelium", "actinide", 11, 9, 1949),
    ElementData(98, "Cf", "Californium", "actinide", 12, 9, 1950),
    ElementData(99, "Es", "Einsteinium", "actinide", 13, 9, 1952),
    ElementData(100, "Fm", "Fermium", "actinide", 14, 9, 1952),
    ElementData(101, "Md", "Mendelevium", "actinide", 15, 9, 1955),
    ElementData(102, "No", "Nobelium", "actinide", 16, 9, 1966),
    ElementData(103, "Lr", "Lawrencium", "actinide", 17, 9, 1961),
]
# fmt: on

assert len(ELEMENTS) == 118, f"Expected 118 elements, got {len(ELEMENTS)}"
