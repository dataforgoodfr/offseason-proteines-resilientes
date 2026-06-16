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

    # ----------------------------------------------------------------------
    # Root categories
    # ----------------------------------------------------------------------
    ALTERNATIVES = "Alternatives végétales"
    CEREALES = "Céréales et pseudo-céréales"
    LEGUMES = "Légumes et assimilés"
    LEGUMINEUSES = "Légumineuses"
    NOIX = "Noix et graines"
    OEUFS_PRODUITS_LAITIERS = "Œufs et produits laitiers"
    POISSONS = "Poissons et fruits de mer"
    POUDRES = "Poudres protéinées"
    SOJA = "Produits à base de soja"
    UNKNOWN = "Unknown"
    VIANDES = "Viandes"

    # ----------------------------------------------------------------------
    # Viandes
    # ----------------------------------------------------------------------
    AIGUILLETTES_DINDE = "Aiguillettes de dinde"
    BLANC_DE_DINDE_TRANCHES = "Blanc de dinde (tranches)"
    CHIPOLATAS = "Chipolatas"
    CONFIT_DE_CANARD = "Confit de canard"
    CORDON_BLEU = "Cordon bleu"
    COTES_AGNEAU = "Côtes d'agneau"
    COTES_DE_PORC = "Côtes de porc"
    CUISSE_POULET = "Cuisse de poulet"
    ENTRECOTE_BOEUF = "Entrecôte bœuf"
    ESCALOPES_DE_DINDE = "Escalopes de dinde"
    ESCALOPE_DE_VEAU = "Escalope de veau"
    FILET_MIGNON_DE_PORC = "Filet mignon de porc"
    GIGOT_AGNEAU = "Gigot d'agneau"
    JAMBON_BLANC = "Jambon blanc"
    JAMBON_CRU = "Jambon cru"
    LAPIN = "Lapin"
    LARDONS = "Lardons"
    MAGRET_DE_CANARD = "Magret de canard"
    MERGUEZ = "Merguez"
    NUGGETS = "Nuggets"
    POITRINE_FUMEE_BACON = "Poitrine fumée / bacon"
    POULET_FERMIER = "Poulet fermier"
    POULET_FILET = "Filet de poulet"
    RILLETTES = "Rillettes"
    ROTI_DE_BOEUF = "Rôti de bœuf"
    ROTI_DE_PORC = "Rôti de porc"
    SAUCISSE_DE_STRASBOURG_KNACKI = "Saucisse de Strasbourg / Knacki"
    SAUCISSON_SEC = "Saucisson sec"
    SAUTE_DE_VEAU = "Sauté de veau"
    STEAK_HACHE_BOEUF = "Steak haché bœuf"

    # ----------------------------------------------------------------------
    # Poissons et fruits de mer
    # ----------------------------------------------------------------------
    ANCHOIS = "Anchois"
    CABILLAUD = "Dos de cabillaud"
    COLIN_PANE = "Colin pané"
    CREVETTES = "Crevettes entières"
    LIMANDE = "Filet de limande"
    MAQUEREAU_CONSERVE = "Maquereau (conserve)"
    MAQUEREAU_FRAIS = "Maquereau frais"
    NOIX_DE_SAINT_JACQUES = "Noix de saint-jacques"
    SARDINES = "Sardines (conserve)"
    SARDINES_FRAICHES = "Sardines fraiches"
    SAUMON = "Pavé de saumon"
    SAUMON_FUME = "Saumon fumé"
    SURIMI = "Bâtonnets de surimi"
    THON = "Thon (conserve)"
    THON_FRAIS = "Thon frais"
    TRUITE_FUMEE = "Truité fumée"

    # ----------------------------------------------------------------------
    # Œufs et produits laitiers
    # ----------------------------------------------------------------------
    BRIE = "Brie"
    BUCHE_DE_CHEVRE = "Bûche de chèvre"
    CAMEMBERT = "Camembert"
    COMTE = "Comté"
    COULOMMIERS = "Coulommiers"
    EMMENTAL = "Emmental"
    FETA = "Feta"
    FROMAGE_BLANC = "Fromage blanc nature"
    FROMAGE_RACLETTE = "Fromage à raclette"
    LAIT_DEMI_ECREME = "Lait demi écrémé"
    LAIT_ENTIER = "Lait entier"
    MOZZARELLA = "Mozzarella"
    OEUFS = "Œufs"
    PARMESAN_RAPE = "Parmesan rapé"
    PETITS_SUISSES = "Petits‑suisses"
    ROQUEFORT = "Roquefort"
    SKYR = "Skyr"
    YAOURT_NATURE_0 = "Yaourt nature 0%"

    # ----------------------------------------------------------------------
    # Légumineuses
    # ----------------------------------------------------------------------
    FALAFELS = "Falafels"
    FALAFELS_POUDRE = "Falafels (poudre)"
    FEVES = "Fèves"
    FLAGEOLETS = "Flageolets"
    FLAGEOLETS_CONSERVE = "Flageolets (conserve)"
    GALETTES_DE_LEGUMINEUSES = "Galettes de légumineuses"
    HARICOTS_BLANCS = "Haricots blancs"
    HARICOTS_BLANCS_CONSERVE = "Haricots blancs (conserve)"
    HARICOTS_NOIRS = "Haricots noirs"
    HARICOTS_NOIRS_CONSERVE = "Haricots noirs (conserve)"
    HARICOTS_ROUGES = "Haricots rouges"
    HARICOTS_ROUGES_CONSERVE = "Haricots rouges (conserve)"
    LENTILLES_BLONDES = "Lentilles blondes"
    LENTILLES_BLONDES_CONSERVE = "Lentilles blondes (conserve)"
    LENTILLES_CORAIL = "Lentilles corail"
    LENTILLES_VERTES = "Lentilles vertes"
    LENTILLES_VERTES_CONSERVE = "Lentilles vertes (conserve)"
    LUPIN = "Lupin (conserve)"
    POIS_CASSES = "Pois cassés"
    POIS_CHICHES = "Pois chiches"
    POIS_CHICHES_CONSERVE = "Pois chiches (conserve)"

    # ----------------------------------------------------------------------
    # Produits à base de soja
    # ----------------------------------------------------------------------
    PROTEINES_SOJA_TEXTUREES = "Protéines de soja texturées"
    TEMPEH = "Tempeh"
    TOFU_FUME = "Tofu (ferme) fumé"
    TOFU_NATURE = "Tofu (ferme) nature"

    # ----------------------------------------------------------------------
    # Légumes et assimilés
    # ----------------------------------------------------------------------
    FRUIT_DU_JACQUER = "Fruit du jacquier"

    # ----------------------------------------------------------------------
    # Céréales et pseudo‑céréales
    # ----------------------------------------------------------------------
    AMARANTE = "Amarante"
    BLE_COMPLET = "Blé complet"
    FLOCON_DAVOINE = "Avoine (flocons)"
    QUINOA = "Quinoa"
    SARRASIN = "Sarrasin"
    SEIGLE = "Seigle"
    SEITAN = "Seitan"

    # ----------------------------------------------------------------------
    # Noix et graines
    # ----------------------------------------------------------------------
    AMANDES = "Amandes"
    BEURRE_DE_CACAHUETE = "Beurre de cacahuète"
    CACAHUETES = "Cacahuètes"
    GRANES_CHIA = "Graines de chia"
    GRANES_COURGE = "Graines de courge"
    GRANES_LIN = "Graines de lin"
    GRANES_TOURNESOL = "Graines de tournesol"
    NOISETTES = "Noisettes"
    NOIX_CAJOUS = "Noix de cajou"
    PIGNONS_PIN = "Pignons de pin"
    PISTACHES = "Pistaches"

    # ----------------------------------------------------------------------
    # Poudres protéinées
    # ----------------------------------------------------------------------
    BARRES_PROTEINEES = "Barres protéinées"
    CASEINE = "Caséine"
    ISOLAT_WHEY = "Isolat de whey"
    PROTEINES_VEGETALES_POUDRE = "Protéines végétales poudre"

    # ----------------------------------------------------------------------
    # Alternatives végétales
    # ----------------------------------------------------------------------
    AIGUILLETTES_VEGETALES = "Aiguillettes végétales"
    BASTONETS_POISSON_VEGETAUX = 'Bâtonnets "poisson" panés végétaux'
    BASTONETS_POISSON_VEGETAUX_CONSERVE = (
        'Bâtonnets "poisson" panés végétaux (conserve)'
    )
    BOULETTES_VEGETALES = "Boulettes végétales"
    BOULETTES_VEGETALES_SURGELE = "Boulettes végétales (surgelé)"
    ESCALOPES_VEGETALES_PANEES = "Escalopes végétales panées"
    GALETTE_VEGETALE_CEREALES = "Galette végétale (céréales)"
    GALETTE_VEGETALE_CEREALES_SURGELE = "Galette végétale (céréales) (surgelé)"
    JAMBON_VEGETAL = "Jambon végétal"
    KNAX_VEGETALES = "Knax végétales"
    LARDONS_VEGETAUX = "Lardons végétaux"
    NUGGETS_VEGETAUX = "Nuggets végétaux"
    NUGGETS_VEGETAUX_SURGELE = "Nuggets végétaux (surgelé)"
    SAUCISSES_VEGETALES = "Saucisses végétales"
    SIMILI_THON = "Simili thon"
    STEAK_VEGETAL = "Steak végétal"
    STEAK_VEGETAL_SURGELE = "Steak végétal surgelé"
    SUPREME_FAUX_POULET = "Suprème de faux poulet"

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
    # ----------------------------------------------------------------------
    # Viandes
    # ----------------------------------------------------------------------
    CategoryValues.AIGUILLETTES_DINDE: CategoryValues.VIANDES,
    CategoryValues.BLANC_DE_DINDE_TRANCHES: CategoryValues.VIANDES,
    CategoryValues.CHIPOLATAS: CategoryValues.VIANDES,
    CategoryValues.CONFIT_DE_CANARD: CategoryValues.VIANDES,
    CategoryValues.CORDON_BLEU: CategoryValues.VIANDES,
    CategoryValues.COTES_AGNEAU: CategoryValues.VIANDES,
    CategoryValues.COTES_DE_PORC: CategoryValues.VIANDES,
    CategoryValues.CUISSE_POULET: CategoryValues.VIANDES,
    CategoryValues.ENTRECOTE_BOEUF: CategoryValues.VIANDES,
    CategoryValues.ESCALOPES_DE_DINDE: CategoryValues.VIANDES,
    CategoryValues.ESCALOPE_DE_VEAU: CategoryValues.VIANDES,
    CategoryValues.FILET_MIGNON_DE_PORC: CategoryValues.VIANDES,
    CategoryValues.GIGOT_AGNEAU: CategoryValues.VIANDES,
    CategoryValues.JAMBON_BLANC: CategoryValues.VIANDES,
    CategoryValues.JAMBON_CRU: CategoryValues.VIANDES,
    CategoryValues.LAPIN: CategoryValues.VIANDES,
    CategoryValues.LARDONS: CategoryValues.VIANDES,
    CategoryValues.MAGRET_DE_CANARD: CategoryValues.VIANDES,
    CategoryValues.MERGUEZ: CategoryValues.VIANDES,
    CategoryValues.NUGGETS: CategoryValues.VIANDES,
    CategoryValues.POITRINE_FUMEE_BACON: CategoryValues.VIANDES,
    CategoryValues.POULET_FERMIER: CategoryValues.VIANDES,
    CategoryValues.POULET_FILET: CategoryValues.VIANDES,
    CategoryValues.RILLETTES: CategoryValues.VIANDES,
    CategoryValues.ROTI_DE_BOEUF: CategoryValues.VIANDES,
    CategoryValues.ROTI_DE_PORC: CategoryValues.VIANDES,
    CategoryValues.SAUCISSE_DE_STRASBOURG_KNACKI: CategoryValues.VIANDES,
    CategoryValues.SAUCISSON_SEC: CategoryValues.VIANDES,
    CategoryValues.SAUTE_DE_VEAU: CategoryValues.VIANDES,
    CategoryValues.STEAK_HACHE_BOEUF: CategoryValues.VIANDES,
    # ----------------------------------------------------------------------
    # Poissons et fruits de mer
    # ----------------------------------------------------------------------
    CategoryValues.ANCHOIS: CategoryValues.POISSONS,
    CategoryValues.CABILLAUD: CategoryValues.POISSONS,
    CategoryValues.COLIN_PANE: CategoryValues.POISSONS,
    CategoryValues.CREVETTES: CategoryValues.POISSONS,
    CategoryValues.LIMANDE: CategoryValues.POISSONS,
    CategoryValues.MAQUEREAU_CONSERVE: CategoryValues.POISSONS,
    CategoryValues.MAQUEREAU_FRAIS: CategoryValues.POISSONS,
    CategoryValues.NOIX_DE_SAINT_JACQUES: CategoryValues.POISSONS,
    CategoryValues.SARDINES: CategoryValues.POISSONS,
    CategoryValues.SARDINES_FRAICHES: CategoryValues.POISSONS,
    CategoryValues.SAUMON: CategoryValues.POISSONS,
    CategoryValues.SAUMON_FUME: CategoryValues.POISSONS,
    CategoryValues.SURIMI: CategoryValues.POISSONS,
    CategoryValues.THON: CategoryValues.POISSONS,
    CategoryValues.THON_FRAIS: CategoryValues.POISSONS,
    CategoryValues.TRUITE_FUMEE: CategoryValues.POISSONS,
    # ----------------------------------------------------------------------
    # Œufs et produits laitiers
    # ----------------------------------------------------------------------
    CategoryValues.BRIE: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.BUCHE_DE_CHEVRE: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.CAMEMBERT: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.COMTE: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.COULOMMIERS: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.EMMENTAL: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.FETA: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.FROMAGE_BLANC: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.FROMAGE_RACLETTE: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.LAIT_DEMI_ECREME: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.LAIT_ENTIER: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.MOZZARELLA: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.OEUFS: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.PARMESAN_RAPE: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.PETITS_SUISSES: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.ROQUEFORT: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.SKYR: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    CategoryValues.YAOURT_NATURE_0: CategoryValues.OEUFS_PRODUITS_LAITIERS,
    # ----------------------------------------------------------------------
    # Légumineuses
    # ----------------------------------------------------------------------
    CategoryValues.FALAFELS: CategoryValues.LEGUMINEUSES,
    CategoryValues.FALAFELS_POUDRE: CategoryValues.LEGUMINEUSES,
    CategoryValues.FEVES: CategoryValues.LEGUMINEUSES,
    CategoryValues.FLAGEOLETS: CategoryValues.LEGUMINEUSES,
    CategoryValues.FLAGEOLETS_CONSERVE: CategoryValues.LEGUMINEUSES,
    CategoryValues.GALETTES_DE_LEGUMINEUSES: CategoryValues.LEGUMINEUSES,
    CategoryValues.HARICOTS_BLANCS: CategoryValues.LEGUMINEUSES,
    CategoryValues.HARICOTS_BLANCS_CONSERVE: CategoryValues.LEGUMINEUSES,
    CategoryValues.HARICOTS_NOIRS: CategoryValues.LEGUMINEUSES,
    CategoryValues.HARICOTS_NOIRS_CONSERVE: CategoryValues.LEGUMINEUSES,
    CategoryValues.HARICOTS_ROUGES: CategoryValues.LEGUMINEUSES,
    CategoryValues.HARICOTS_ROUGES_CONSERVE: CategoryValues.LEGUMINEUSES,
    CategoryValues.LENTILLES_BLONDES: CategoryValues.LEGUMINEUSES,
    CategoryValues.LENTILLES_BLONDES_CONSERVE: CategoryValues.LEGUMINEUSES,
    CategoryValues.LENTILLES_CORAIL: CategoryValues.LEGUMINEUSES,
    CategoryValues.LENTILLES_VERTES: CategoryValues.LEGUMINEUSES,
    CategoryValues.LENTILLES_VERTES_CONSERVE: CategoryValues.LEGUMINEUSES,
    CategoryValues.LUPIN: CategoryValues.LEGUMINEUSES,
    CategoryValues.POIS_CASSES: CategoryValues.LEGUMINEUSES,
    CategoryValues.POIS_CHICHES: CategoryValues.LEGUMINEUSES,
    CategoryValues.POIS_CHICHES_CONSERVE: CategoryValues.LEGUMINEUSES,
    # ----------------------------------------------------------------------
    # Produits à base de soja
    # ----------------------------------------------------------------------
    CategoryValues.PROTEINES_SOJA_TEXTUREES: CategoryValues.SOJA,
    CategoryValues.TEMPEH: CategoryValues.SOJA,
    CategoryValues.TOFU_FUME: CategoryValues.SOJA,
    CategoryValues.TOFU_NATURE: CategoryValues.SOJA,
    # ----------------------------------------------------------------------
    # Légumes et assimilés
    # ----------------------------------------------------------------------
    CategoryValues.FRUIT_DU_JACQUER: CategoryValues.LEGUMES,
    # ----------------------------------------------------------------------
    # Céréales et pseudo‑céréales
    # ----------------------------------------------------------------------
    CategoryValues.AMARANTE: CategoryValues.CEREALES,
    CategoryValues.BLE_COMPLET: CategoryValues.CEREALES,
    CategoryValues.FLOCON_DAVOINE: CategoryValues.CEREALES,
    CategoryValues.QUINOA: CategoryValues.CEREALES,
    CategoryValues.SARRASIN: CategoryValues.CEREALES,
    CategoryValues.SEIGLE: CategoryValues.CEREALES,
    CategoryValues.SEITAN: CategoryValues.CEREALES,
    # ----------------------------------------------------------------------
    # Noix et graines
    # ----------------------------------------------------------------------
    CategoryValues.AMANDES: CategoryValues.NOIX,
    CategoryValues.BEURRE_DE_CACAHUETE: CategoryValues.NOIX,
    CategoryValues.CACAHUETES: CategoryValues.NOIX,
    CategoryValues.GRANES_CHIA: CategoryValues.NOIX,
    CategoryValues.GRANES_COURGE: CategoryValues.NOIX,
    CategoryValues.GRANES_LIN: CategoryValues.NOIX,
    CategoryValues.GRANES_TOURNESOL: CategoryValues.NOIX,
    CategoryValues.NOISETTES: CategoryValues.NOIX,
    CategoryValues.NOIX_CAJOUS: CategoryValues.NOIX,
    CategoryValues.PIGNONS_PIN: CategoryValues.NOIX,
    CategoryValues.PISTACHES: CategoryValues.NOIX,
    # ----------------------------------------------------------------------
    # Poudres protéinées
    # ----------------------------------------------------------------------
    CategoryValues.BARRES_PROTEINEES: CategoryValues.POUDRES,
    CategoryValues.CASEINE: CategoryValues.POUDRES,
    CategoryValues.ISOLAT_WHEY: CategoryValues.POUDRES,
    CategoryValues.PROTEINES_VEGETALES_POUDRE: CategoryValues.POUDRES,
    # ----------------------------------------------------------------------
    # Alternatives végétales
    # ----------------------------------------------------------------------
    CategoryValues.AIGUILLETTES_VEGETALES: CategoryValues.ALTERNATIVES,
    CategoryValues.BASTONETS_POISSON_VEGETAUX: CategoryValues.ALTERNATIVES,
    CategoryValues.BASTONETS_POISSON_VEGETAUX_CONSERVE: CategoryValues.ALTERNATIVES,
    CategoryValues.BOULETTES_VEGETALES: CategoryValues.ALTERNATIVES,
    CategoryValues.BOULETTES_VEGETALES_SURGELE: CategoryValues.ALTERNATIVES,
    CategoryValues.ESCALOPES_VEGETALES_PANEES: CategoryValues.ALTERNATIVES,
    CategoryValues.GALETTE_VEGETALE_CEREALES: CategoryValues.ALTERNATIVES,
    CategoryValues.GALETTE_VEGETALE_CEREALES_SURGELE: CategoryValues.ALTERNATIVES,
    CategoryValues.JAMBON_VEGETAL: CategoryValues.ALTERNATIVES,
    CategoryValues.KNAX_VEGETALES: CategoryValues.ALTERNATIVES,
    CategoryValues.LARDONS_VEGETAUX: CategoryValues.ALTERNATIVES,
    CategoryValues.NUGGETS_VEGETAUX: CategoryValues.ALTERNATIVES,
    CategoryValues.NUGGETS_VEGETAUX_SURGELE: CategoryValues.ALTERNATIVES,
    CategoryValues.SAUCISSES_VEGETALES: CategoryValues.ALTERNATIVES,
    CategoryValues.SIMILI_THON: CategoryValues.ALTERNATIVES,
    CategoryValues.STEAK_VEGETAL: CategoryValues.ALTERNATIVES,
    CategoryValues.STEAK_VEGETAL_SURGELE: CategoryValues.ALTERNATIVES,
    CategoryValues.SUPREME_FAUX_POULET: CategoryValues.ALTERNATIVES,
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
