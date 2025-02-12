import os
import json
import math

from enum import StrEnum
from typing import Optional, NamedTuple
from dataclasses import dataclass, field

CWD = os.getcwd()

Inss_Range = NamedTuple("Inss_Range", [("initial", float), ("final", float), ("aliquot", float)])
Income_Tax_Range = NamedTuple("Income_Tax_Range", [("initial", float), ("final", float), ("aliquot", float), ("monthly_deduction", float)])

type ISO_Date_Format = str
type Inss_Table = dict[ISO_Date_Format, dict[str, Inss_Range]]
type Income_Tax_Table = dict[ISO_Date_Format, dict[str, Income_Tax_Range]]

class Currency(StrEnum):
    Real = "Real (R$)"
    Dollar = "Dollar (US$)"

inss_table = {
    "first_band": Inss_Range(0.0, 1518.0, 0.075),
    "second_band": Inss_Range(1518.01, 2793.88, 0.09),
    "third_band": Inss_Range(2793.89, 4190.83, 0.12),
    "foruth_band": Inss_Range(4190.84, 8157.41, 0.14)
}

income_tax_table = {
    "first_band": Income_Tax_Range(0.0, 2259.20, 0.0, 0.0),
    "second_band": Income_Tax_Range(2259.21, 2828.65, 0.075, 169.44),
    "third_band": Income_Tax_Range(2828.66, 3751.05, 0.15, 381.44),
    "fourth_band": Income_Tax_Range(3751.06, 4664.68, 0.225, 662.77),
    "fith_band": Income_Tax_Range(4664.69, math.inf, 0.275, 896.00)
}

def inss_deduction_calculation(gross_salary: float, inss_table: Inss_Table) -> float:
    aliquot_sum: float = 0.0
    for inss_range in inss_table.values():
        if gross_salary >= inss_range.final:
            aliquot_sum += (inss_range.final - inss_range.initial) * inss_range.aliquot
        else:
            aliquot_sum += (gross_salary - inss_range.initial) * inss_range.aliquot
    return aliquot_sum

def income_tax_deduction_calculation(gross_salary: float, income_tax_table: Income_Tax_Table, inss_deduction: float) -> float:
    income_tax_sum: float = 0.0
    for income_tax_range in income_tax_table.values():
        if income_tax_range.initial <= gross_salary and gross_salary <= income_tax_range.final:
            income_tax_sum = ((gross_salary - inss_deduction) * income_tax_range.aliquot) - income_tax_range.monthly_deduction
            break
    return income_tax_sum

@dataclass
class Static_Financial_Status:
    latest: bool
    starting_date: ISO_Date_Format
    ending_date: ISO_Date_Format
    gross_salary: float
    net_salary: float = field(init=False)
    inss_table: Inss_Table
    inss_deduction: float = field(init=False)
    income_tax_table: Income_Tax_Table
    income_tax_deduction: float = field(init=False)
    salary_currency: Currency
    working_hours_per_day: float = field(repr=False)

    def __post_init__(self):
        self.inss_deduction = inss_deduction_calculation(self.gross_salary, self.inss_table)
        self.income_tax_deduction = income_tax_deduction_calculation(self.gross_salary, self.income_tax_table, self.inss_deduction)
        self.net_salary = self.gross_salary - self.inss_deduction - self.income_tax_deduction

    def to_json(self) -> dict[str, bool | str | float]:
        return {
            "latest": self.latest,
            "salary_currency": self.salary_currency.value,
            "starting_date": self.starting_date,
            "ending_date": self.ending_date,
            "gross_salary": self.gross_salary,
            "net_salary": self.net_salary,
            "inss_deduction": self.inss_deduction,
            "income_tax_deduction": self.income_tax_deduction
        }

@dataclass
class Volatile_Financial_Status:
    ...

if __name__ == "__main__":
    filename: str = "financial_data.json"
    filename_path: str = os.path.join(CWD, filename)
    if not os.path.exists(filename_path):
        with open(filename_path, "w") as stream:
            json.dump({}, stream)

    financial_status = Static_Financial_Status(
        latest=True,
        starting_date="2024-01-01",
        ending_date="2025-01-01",
        gross_salary=10_000.0,
        income_tax_table=income_tax_table,
        inss_table=inss_table,
        working_hours_per_day=8.0,
        salary_currency=Currency.Real
    )

    with open(filename_path, "w") as stream:
        json.dump(financial_status.to_json(), stream, indent=4)

