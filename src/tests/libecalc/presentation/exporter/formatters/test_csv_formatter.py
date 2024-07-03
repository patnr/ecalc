from dataclasses import dataclass
from typing import List, Union

from libecalc.common.units import Unit
from libecalc.domain.tabular.tabular import ColumnIndex
from libecalc.presentation.exporter.formatters.formatter import (
    CSVFormatter,
    Formattable,
)


@dataclass
class Column:
    id: str
    title: str
    unit: Unit = Unit.TONS

    def get_title(self) -> str:
        return f"{self.title}[{self.unit}]"


@dataclass
class Data(Formattable):
    rows: List[str]
    columns: List[str]
    value: int

    def get_column(self, column_id: ColumnIndex) -> Column:
        return Column(
            id=column_id,
            title=column_id.upper(),
        )

    @property
    def row_ids(self) -> List[str]:
        return self.rows

    @property
    def column_ids(self) -> List[str]:
        return self.columns

    def get_value(self, row_id: str, column_id: str) -> Union[int, float]:
        return self.value


class TestCSVFormatter:
    def test_format_comma(self):
        formatter = CSVFormatter()
        rows = formatter.format(
            Data(
                rows=["row1", "row2"],
                columns=["col1", "col2"],
                value=5,
            )
        )

        assert rows == [
            "col1,col2",
            "#COL1[t],COL2[t]",
            "5,5",
            "5,5",
        ]

    def test_format_tabs(self):
        formatter = CSVFormatter(separation_character="\t")
        rows = formatter.format(
            Data(
                rows=["row1", "row2"],
                columns=["col1", "col2"],
                value=5,
            )
        )

        assert rows == [
            "col1\tcol2",
            "#COL1[t]\tCOL2[t]",
            "5\t5",
            "5\t5",
        ]
