import sqlalchemy as sa

from .language import ByLanguage, Language
from ..core import TableBase


class Generation(TableBase, ByLanguage):
    """One iteration of the Pokémon series.

    For example, the original 151 Pokémon and the games Red, Blue, and Yellow
    all belong to Generation 1.  The next 100 Pokémon and Gold, Silver, and
    Crystal belong to Generation 2, and so on.

    The term "generation" is unofficial, but is used almost universally within
    the fandom.
    """

    __tablename__ = 'generations'

    _by_language_class_name = 'GenerationName'

    id = sa.Column(sa.Integer, primary_key=True)
    identifier = sa.Column(sa.Unicode, unique=True, nullable=False)
    is_base_series = sa.Column(
        sa.Boolean, nullable=False,
        doc="""True if this is a traditional generation; False for Let's Go.

        Let's Go is officially part of the main series (we wouldn't be covering
        it otherwise), but it functions differently enough that we need *some*
        sort of term to distinguish it.
        """
    )
    release_order = sa.Column(sa.Integer, unique=True, nullable=False)
    type_chart_id = sa.Column(sa.ForeignKey('type_charts.id'), nullable=False)

class GenerationName(TableBase):
    """A generation's name in a particular language.

    As generations are unofficial, so are these names.
    """

    __tablename__ = 'generation_names'

    language_id = sa.Column(sa.ForeignKey(Language.id), primary_key=True)
    generation_id = sa.Column(sa.ForeignKey(Generation.id), primary_key=True)
    name = sa.Column(sa.Text, nullable=False)

    __table_args__ = (sa.UniqueConstraint('language_id', 'name')),

class Game(TableBase):
    """One of the main-series Pokémon games."""

    __tablename__ = 'games'
    __table_args__ = (sa.UniqueConstraint('id', 'generation_id'),)

    id = sa.Column(sa.Integer, primary_key=True)
    identifier = sa.Column(sa.Unicode, unique=True, nullable=False)
    generation_id = sa.Column(sa.Integer, sa.ForeignKey('generations.id'),
                              nullable=False)
