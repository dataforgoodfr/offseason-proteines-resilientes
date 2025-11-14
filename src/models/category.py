from enum import StrEnum, unique
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.engine import Connection
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship
from sqlalchemy.sql.schema import Table

from .base import Base

# To avoid circular imports.
if TYPE_CHECKING:
    from .product import Product


@unique
class CategoryValues(StrEnum):
    """
    The normalised categories of the product.
    """

    # Root categories.
    ALTERNATIVE = "Alternatives végétales"
    CEREALE = "Céréales et pseudo-céréales"
    LAITIER = "Œufs et produits laitiers"
    LEGUME = "Légumes et assimilés"
    LEGUMINEUSE = "Légumineuses"
    NOIX = "Noix et graines"
    POISSON = "Poissons et fruits de mer"
    POUDRE = "Poudres protéinées"
    SOJA = "Produits à base de soja"
    VIANDE = "Viandes"
    UNKNOWN = "Unknown"

    # Viandes
    AGNEAU = "Agneau"
    AIGUILLETTES_DINDE = "Aiguillettes de dinde"
    BLANC_DE_DINDE_TRANCHES = "Blanc de dinde (tranches)"
    CHIPOLATAS = "Chipolatas"
    CONFIT_DE_CANARD = "Confit de canard"
    CORDONS_BLEUS = "Cordons bleus"
    COTES_DE_PORC = "Côtes de porc"
    CUISSE_POULET = "Cuisse poulet"
    ENTRECOTE_BOEUF = "Entrecôte bœuf"
    ESCALOPES_DE_DINDE = "Escalopes de dinde"
    ESCALOPE_DE_VEAU = "Escalope de veau"
    FILET_MIGNON_DE_PORC = "Filet mignon de porc"
    JAMBON_BLANC = "Jambon blanc"
    JAMBON_CRU = "Jambon cru"
    LAPIN = "Lapin"
    LARDONS = "Lardons"
    MAGRET_DE_CANARD = "Magret de canard"
    MERGUEZ = "Merguez"
    NUGGETS = "Nuggets"
    POITRINE_FUMEE_BACON = "Poitrine fumée / bacon"
    POULET_FERMIER = "Poulet fermier"
    POULET_FILET = "Filet / escalope (poulet)"
    RILLETTES = "Rillettes"
    ROTI_DE_BOEUF = "Rôti de bœuf"
    ROTI_DE_PORC = "Rôti de porc"
    SAUCISSE_DE_STRASBOURG_KNACKI = "Saucisse de Strasbourg / Knacki"
    SAUCISSON_SEC = "Saucisson sec"
    SAUTE_DE_VEAU = "Sauté de veau"
    STEAK_HACHE_BOEUF = "Steak haché bœuf"
    TOURNEDOS_BOEUF = "Tournedos bœuf"

    # Poissons et fruits de mer
    ANCHOIS = "Anchois"
    CABILLAUD = "Cabillaud"
    COLIN_PANE = "Colin pané"
    CREVETTES = "Crevettes"
    LIMANDE = "Limande"
    MAQUEREAU = "Maquereau"
    NOIX_DE_SAINT_JACQUES = "Noix de Saint-Jacques"
    SARDINES = "Sardines"
    SAUMON = "Saumon"
    SAUMON_FUME = "Saumon fumé"
    SURIMI = "Surimi"
    THON = "Thon"
    TRUITE_FUMEE = "Truité fumée"

    # Œufs et produits laitiers
    BRIE = "Brie"
    BUCHE_DE_CHEVRE = "Bûche de chèvre"
    CAMEMBERT = "Camembert"
    COMTE = "Comté"
    COULOMMIERS = "Coulommiers"
    EMMENTAL = "Emmental"
    FETA = "Feta"
    FROMAGE_A_RACLETTE = "Fromage à raclette"
    FROMAGE_BLANC = "Fromage blanc"
    FROMAGE_FRAIS = "Fromage frais"
    LAIT_DEMI_ECREME = "Lait demi ecrémé"
    LAIT_ENTIER = "Lait entier"
    MOZZARELLA = "Mozzarella"
    OEUFS = "Œufs"
    PARMESAN_RAPE = "Parmesan rapé"
    PETITS_SUISSES = "Petits-suisses"
    ROQUEFORT = "Roquefort"
    SKYR = "Skyr"
    YAOURT_AROMATISE = "Yaourt aromatisé"
    YAOURT_NATURE_0 = "Yaourt nature 0%"

    # Légumineuses
    FALAFELS = "Falafels"
    FEVEROLES = "Féveroles"
    FEVES = "Fèves"
    FLAGEOLETS = "Flageolets"
    GALETTES_DE_LEGUMINEUSES = "Galettes de légumineuses"
    HARICOTS_BLANCS = "Haricots blancs"
    HARICOTS_NOIRS = "Haricots noirs"
    HARICOTS_ROUGES = "Haricots rouges"
    LENTILLES_BLONDES = "Lentilles blondes"
    LENTILLES_CORAIL = "Lentilles corail"
    LENTILLES_VERTES = "Lentilles vertes"
    LUPIN = "Lupin"
    POIS_CASSES = "Pois cassés"
    POIS_CHICHES = "Pois chiches"

    # Produits à base de soja
    PROTEINES_DE_SOJA_TEXTUREES = "Protéines de soja texturées"
    TEMPEH = "Tempeh"
    TOFU_FUME = "Tofu fumé"
    TOFU_NATURE = "Tofu nature"

    # Légumes et assimilés
    FRUIT_DU_JACQUER = "Fruit du jacquier"

    # Céréales et pseudo‑céréales
    AMARANTE = "Amarante"
    BLE_COMPLET = "Blé complet"
    FLOCON_DAVOINE = "Flocon d'avoine"
    GERME_DE_BLE = "Germe de blé"
    QUINOA = "Quinoa"
    SARRASIN = "Sarrasin"
    SEIGLE = "Seigle"
    SEITAN = "Seitan"
    SON_DAVOINE = "Son d'avoine"

    # Noix et graines
    AMANDES = "Amandes"
    BEURRE_DE_CACAHUETE = "Beurre de cacahuète"
    CACAHUETES = "Cacahuètes"
    GRAINES_DE_CHIA = "Graines de chia"
    GRAINES_DE_COURRE = "Graines de courge"
    GRAINES_DE_LIN = "Graines de lin"
    GRAINES_DE_TOURNESOL = "Graines de tournesol"
    NOISETTES = "Noisettes"
    NOIX_DE_CAJOUS = "Noix de cajou"
    PINCONS_DE_PIN = "Pignons de pin"
    PISTACHES = "Pistaches"

    # Poudres protéinées
    BARRES_PROTEINEES = "Barres protéinées"
    CASEINE = "Caséine"
    ISOLAT_DE_WHEY = "Isolat de whey"
    PROTEINES_VEGETALES_POIS_RIZ = "Protéines végétales (pois, riz)"

    # Alternatives végétales
    AIGUILLETTES_VEGETALES = "Aiguillettes végétales"
    BASTONETS_POISSON_VEGETAUX = "Bâtonnets poisson végétaux"
    BOULETTES_VEGETALES = "Boulettes végétales"
    ESCALOPES_VEGETALES_PANEES = "Escalopes végétales panées"
    JAMBON_VEGETAL = "Jambon végétal"
    LARDONS_VEGETAUX = "Lardons végétaux"
    NUGGETS_VEGETAUX = "Nuggets végétales"
    SAUCISSES_VEGETALES = "Saucisses végétales"
    SIMILI_THON = "Simili thon"
    STEAKS_VEGETAUX = "Steaks végétaux"

    @classmethod
    def _missing_(cls, value):
        """
        Invoked when the value is not found in the enum. It is used here to
        accept values in a case-insensitive way.

        See https://docs.python.org/3/library/enum.html#enum.Enum._missing_.
        """

        value = value.upper()

        for member in cls:
            if member.value.upper() == value:
                return member

        return None


# Mapping of categories to their allowed subcategories.
#
# If a category is not present in this dictionary, it is considered as a root
# category.
CATEGORY_SUBCATEGORY_MAP: Dict[CategoryValues, CategoryValues] = {
    # Viandes
    CategoryValues.AGNEAU: CategoryValues.VIANDE,
    CategoryValues.AIGUILLETTES_DINDE: CategoryValues.VIANDE,
    CategoryValues.BLANC_DE_DINDE_TRANCHES: CategoryValues.VIANDE,
    CategoryValues.CHIPOLATAS: CategoryValues.VIANDE,
    CategoryValues.CONFIT_DE_CANARD: CategoryValues.VIANDE,
    CategoryValues.CORDONS_BLEUS: CategoryValues.VIANDE,
    CategoryValues.COTES_DE_PORC: CategoryValues.VIANDE,
    CategoryValues.CUISSE_POULET: CategoryValues.VIANDE,
    CategoryValues.ENTRECOTE_BOEUF: CategoryValues.VIANDE,
    CategoryValues.ESCALOPES_DE_DINDE: CategoryValues.VIANDE,
    CategoryValues.ESCALOPE_DE_VEAU: CategoryValues.VIANDE,
    CategoryValues.FILET_MIGNON_DE_PORC: CategoryValues.VIANDE,
    CategoryValues.JAMBON_BLANC: CategoryValues.VIANDE,
    CategoryValues.JAMBON_CRU: CategoryValues.VIANDE,
    CategoryValues.LAPIN: CategoryValues.VIANDE,
    CategoryValues.LARDONS: CategoryValues.VIANDE,
    CategoryValues.MAGRET_DE_CANARD: CategoryValues.VIANDE,
    CategoryValues.MERGUEZ: CategoryValues.VIANDE,
    CategoryValues.NUGGETS: CategoryValues.VIANDE,
    CategoryValues.POITRINE_FUMEE_BACON: CategoryValues.VIANDE,
    CategoryValues.POULET_FERMIER: CategoryValues.VIANDE,
    CategoryValues.POULET_FILET: CategoryValues.VIANDE,
    CategoryValues.RILLETTES: CategoryValues.VIANDE,
    CategoryValues.ROTI_DE_BOEUF: CategoryValues.VIANDE,
    CategoryValues.ROTI_DE_PORC: CategoryValues.VIANDE,
    CategoryValues.SAUCISSE_DE_STRASBOURG_KNACKI: CategoryValues.VIANDE,
    CategoryValues.SAUCISSON_SEC: CategoryValues.VIANDE,
    CategoryValues.SAUTE_DE_VEAU: CategoryValues.VIANDE,
    CategoryValues.STEAK_HACHE_BOEUF: CategoryValues.VIANDE,
    CategoryValues.TOURNEDOS_BOEUF: CategoryValues.VIANDE,
    # Poissons et fruits de mer
    CategoryValues.ANCHOIS: CategoryValues.POISSON,
    CategoryValues.CABILLAUD: CategoryValues.POISSON,
    CategoryValues.COLIN_PANE: CategoryValues.POISSON,
    CategoryValues.CREVETTES: CategoryValues.POISSON,
    CategoryValues.LIMANDE: CategoryValues.POISSON,
    CategoryValues.MAQUEREAU: CategoryValues.POISSON,
    CategoryValues.NOIX_DE_SAINT_JACQUES: CategoryValues.POISSON,
    CategoryValues.SARDINES: CategoryValues.POISSON,
    CategoryValues.SAUMON: CategoryValues.POISSON,
    CategoryValues.SAUMON_FUME: CategoryValues.POISSON,
    CategoryValues.SURIMI: CategoryValues.POISSON,
    CategoryValues.THON: CategoryValues.POISSON,
    CategoryValues.TRUITE_FUMEE: CategoryValues.POISSON,
    # Œufs et produits laitiers
    CategoryValues.BRIE: CategoryValues.LAITIER,
    CategoryValues.BUCHE_DE_CHEVRE: CategoryValues.LAITIER,
    CategoryValues.CAMEMBERT: CategoryValues.LAITIER,
    CategoryValues.COMTE: CategoryValues.LAITIER,
    CategoryValues.COULOMMIERS: CategoryValues.LAITIER,
    CategoryValues.EMMENTAL: CategoryValues.LAITIER,
    CategoryValues.FETA: CategoryValues.LAITIER,
    CategoryValues.FROMAGE_A_RACLETTE: CategoryValues.LAITIER,
    CategoryValues.FROMAGE_BLANC: CategoryValues.LAITIER,
    CategoryValues.FROMAGE_FRAIS: CategoryValues.LAITIER,
    CategoryValues.LAIT_DEMI_ECREME: CategoryValues.LAITIER,
    CategoryValues.LAIT_ENTIER: CategoryValues.LAITIER,
    CategoryValues.MOZZARELLA: CategoryValues.LAITIER,
    CategoryValues.OEUFS: CategoryValues.LAITIER,
    CategoryValues.PARMESAN_RAPE: CategoryValues.LAITIER,
    CategoryValues.PETITS_SUISSES: CategoryValues.LAITIER,
    CategoryValues.ROQUEFORT: CategoryValues.LAITIER,
    CategoryValues.SKYR: CategoryValues.LAITIER,
    CategoryValues.YAOURT_AROMATISE: CategoryValues.LAITIER,
    CategoryValues.YAOURT_NATURE_0: CategoryValues.LAITIER,
    # Légumineuses
    CategoryValues.FALAFELS: CategoryValues.LEGUMINEUSE,
    CategoryValues.FEVEROLES: CategoryValues.LEGUMINEUSE,
    CategoryValues.FEVES: CategoryValues.LEGUMINEUSE,
    CategoryValues.FLAGEOLETS: CategoryValues.LEGUMINEUSE,
    CategoryValues.GALETTES_DE_LEGUMINEUSES: CategoryValues.LEGUMINEUSE,
    CategoryValues.HARICOTS_BLANCS: CategoryValues.LEGUMINEUSE,
    CategoryValues.HARICOTS_NOIRS: CategoryValues.LEGUMINEUSE,
    CategoryValues.HARICOTS_ROUGES: CategoryValues.LEGUMINEUSE,
    CategoryValues.LENTILLES_BLONDES: CategoryValues.LEGUMINEUSE,
    CategoryValues.LENTILLES_CORAIL: CategoryValues.LEGUMINEUSE,
    CategoryValues.LENTILLES_VERTES: CategoryValues.LEGUMINEUSE,
    CategoryValues.LUPIN: CategoryValues.LEGUMINEUSE,
    CategoryValues.POIS_CASSES: CategoryValues.LEGUMINEUSE,
    CategoryValues.POIS_CHICHES: CategoryValues.LEGUMINEUSE,
    # Produits à base de soja
    CategoryValues.PROTEINES_DE_SOJA_TEXTUREES: CategoryValues.SOJA,
    CategoryValues.TEMPEH: CategoryValues.SOJA,
    CategoryValues.TOFU_FUME: CategoryValues.SOJA,
    CategoryValues.TOFU_NATURE: CategoryValues.SOJA,
    # Légumes et assimilés
    CategoryValues.FRUIT_DU_JACQUER: CategoryValues.LEGUME,
    # Céréales et pseudo‑céréales
    CategoryValues.AMARANTE: CategoryValues.CEREALE,
    CategoryValues.BLE_COMPLET: CategoryValues.CEREALE,
    CategoryValues.FLOCON_DAVOINE: CategoryValues.CEREALE,
    CategoryValues.GERME_DE_BLE: CategoryValues.CEREALE,
    CategoryValues.QUINOA: CategoryValues.CEREALE,
    CategoryValues.SARRASIN: CategoryValues.CEREALE,
    CategoryValues.SEIGLE: CategoryValues.CEREALE,
    CategoryValues.SEITAN: CategoryValues.CEREALE,
    CategoryValues.SON_DAVOINE: CategoryValues.CEREALE,
    # Noix et graines
    CategoryValues.AMANDES: CategoryValues.NOIX,
    CategoryValues.BEURRE_DE_CACAHUETE: CategoryValues.NOIX,
    CategoryValues.CACAHUETES: CategoryValues.NOIX,
    CategoryValues.GRAINES_DE_CHIA: CategoryValues.NOIX,
    CategoryValues.GRAINES_DE_COURRE: CategoryValues.NOIX,
    CategoryValues.GRAINES_DE_LIN: CategoryValues.NOIX,
    CategoryValues.GRAINES_DE_TOURNESOL: CategoryValues.NOIX,
    CategoryValues.NOISETTES: CategoryValues.NOIX,
    CategoryValues.NOIX_DE_CAJOUS: CategoryValues.NOIX,
    CategoryValues.PINCONS_DE_PIN: CategoryValues.NOIX,
    CategoryValues.PISTACHES: CategoryValues.NOIX,
    # Poudres protéinées
    CategoryValues.BARRES_PROTEINEES: CategoryValues.POUDRE,
    CategoryValues.CASEINE: CategoryValues.POUDRE,
    CategoryValues.ISOLAT_DE_WHEY: CategoryValues.POUDRE,
    CategoryValues.PROTEINES_VEGETALES_POIS_RIZ: CategoryValues.POUDRE,
    # Alternatives végétales
    CategoryValues.AIGUILLETTES_VEGETALES: CategoryValues.ALTERNATIVE,
    CategoryValues.BASTONETS_POISSON_VEGETAUX: CategoryValues.ALTERNATIVE,
    CategoryValues.BOULETTES_VEGETALES: CategoryValues.ALTERNATIVE,
    CategoryValues.ESCALOPES_VEGETALES_PANEES: CategoryValues.ALTERNATIVE,
    CategoryValues.JAMBON_VEGETAL: CategoryValues.ALTERNATIVE,
    CategoryValues.LARDONS_VEGETAUX: CategoryValues.ALTERNATIVE,
    CategoryValues.NUGGETS_VEGETAUX: CategoryValues.ALTERNATIVE,
    CategoryValues.SAUCISSES_VEGETALES: CategoryValues.ALTERNATIVE,
    CategoryValues.SIMILI_THON: CategoryValues.ALTERNATIVE,
    CategoryValues.STEAKS_VEGETAUX: CategoryValues.ALTERNATIVE,
}


class Category(Base):
    """
    Represents the category table in the RDBMS.
    """

    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped["CategoryValues"] = mapped_column(
        Enum(
            CategoryValues,
            values_callable=lambda e: [x.value for x in e],
        )
    )

    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("category.id"))

    parent_category: Mapped["Category"] = relationship(
        remote_side=[id],
        backref="subcategories",
    )
    products: Mapped[List["Product"]] = relationship(back_populates="category")


@listens_for(Category.__table__, "after_create")
def initialise_categories(target: Table, connection: Connection, **kw):
    """
    Initialises the category table with normalised values.

    It is automatically executed when creating the database schema.
    """

    categories: Dict[CategoryValues, Category] = {}

    # First loop to create all Category objects.
    for category in CategoryValues:
        categories[category] = Category(name=str(category))

    # Second loop to map subcategories with their parent category.
    for k, v in CATEGORY_SUBCATEGORY_MAP.items():
        categories[k].parent_category = categories[v]

    session = Session(connection)
    session.add_all(categories.values())
    session.commit()
