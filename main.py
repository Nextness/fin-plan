#!/usr/bin/env python3

from __future__ import annotations

import os
import sys
import json
import math
import uuid
import toml

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from enum import StrEnum
from typing import NamedTuple
from dataclasses import dataclass, field
from collections.abc import Callable

CWD = os.getcwd()

Inss_Range = NamedTuple("Inss_Range", [("initial", float), ("final", float), ("aliquot", float)])
Income_Tax_Range = NamedTuple("Income_Tax_Range", [("initial", float), ("final", float), ("aliquot", float), ("monthly_deduction", float)])

type ISO_Date_Format = str
type Inss_Table = dict[ISO_Date_Format, dict[str, Inss_Range]]
type Income_Tax_Table = dict[ISO_Date_Format, dict[str, Income_Tax_Range]]

type Monthly_Icome_Callable = Callable[[..., float], float]

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
    ending_date: ISO_Date_Format | None
    gross_salary: float
    net_salary: float = field(init=False)
    inss_table: Inss_Table
    inss_deduction: float = field(init=False)
    income_tax_table: Income_Tax_Table
    income_tax_deduction: float = field(init=False)
    salary_currency: Currency
    working_hours_per_day: float = field(repr=False)

    def __post_init__(self):
        if self.latest is None: self.latest = False

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

def run_static_financial_status():
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

def new_card(id: str, card_type: str, card_name: str, payment_type: str, final_number: str):
    return {
        "id": id,
        "type": card_type,
        "name": card_name,
        "payment_type": payment_type,
        "final_number": final_number,
    }

def new_sale(status: str, card_id: str, sale_id: str, name: str, sale_date: str, currency: str, sale_value: float, installments: int):
    return {
        "status": status,
        "card_id": card_id,
        "sale_id": sale_id,
        "name": name,
        "sale_date": sale_date,
        "currency": currency,
        "sale_value": sale_value,
        "installments": installments,
    }

def new_installments(sale):
    installments = sale["installments"]
    sale_value = sale["sale_value"]
    monthly_amount = sale_value / installments
    result = []
    for i in range(installments):
        i += 1
        installment_id = str(uuid.uuid4())
        result.append({
            "sale_id": sale["sale_id"],
            "id": installment_id,
            "installment": i,
            "value": monthly_amount,
            "date": "..."
        })
    return result

def generate_date_range(start: datetime, end: datetime) -> list[datetime]:
    create_date_range: list[datetime] = []
    current = start
    while current <= end:
        create_date_range.append(current)
        current += relativedelta(months=1)
    return create_date_range

def generate_yearly_income_per_month(date_range: list[datetime], total_gross_income: float) -> dict[str, float]:
    result = {}
    for date in date_range:
        key: str = f"{date.year}-{date.month:02}"
        result[key] = total_gross_income
    return result

def estimate_yearly_income_100(**args) -> dict[str, dict[str, float]]:
    assert (start := args.get("start")) is not None, "Expected the field 'start: datetime' but was not found"
    assert (end := args.get("end")) is not None, "Expected the field 'end: datetime' but was not found"
    assert (monthly_gross_salary_income := args.get("monthly_gross_salary_income")) is not None, "Expected the field 'monthly_gross_salary_income: float' but was not found"
    assert (monthly_gross_food_income := args.get("monthly_gross_food_income")) is not None, "Expected the field 'monthly_gross_food_income: float' but was not found"

    yearly_gross_salary_income: float = monthly_gross_salary_income * 12 + monthly_gross_salary_income
    yearly_gross_food_income: float = monthly_gross_food_income * 12
    total_gross_income: float = yearly_gross_salary_income + yearly_gross_food_income

    date_range = generate_date_range(start, end)
    result = generate_yearly_income_per_month(date_range, total_gross_income)
    return result

def estimate_yearly_income_200(**args) -> dict[str, dict[str, float]]:
    assert (start := args.get("start")) is not None, "Expected the field 'start: datetime' but was not found"
    assert (end := args.get("end")) is not None, "Expected the field 'end: datetime' but was not found"
    assert (monthly_gross_salary_income := args.get("monthly_gross_salary_income")) is not None, "Expected the field 'monthly_gross_salary_income: float' but was not found"
    assert (monthly_gross_food_income := args.get("monthly_gross_food_income")) is not None, "Expected the field 'monthly_gross_food_income: float' but was not found"
    assert (monthly_benefit_income := args.get("monthly_benefit_income")) is not None, "Expected the field 'monthly_benefit_income: float' but was not found"

    yearly_gross_salary_income: float = monthly_gross_salary_income * 12 + monthly_gross_salary_income
    yearly_gross_food_income: float = monthly_gross_food_income * 12
    yearly_benefit_income: float = monthly_benefit_income * 12
    total_gross_income: float = yearly_gross_salary_income + yearly_gross_food_income + yearly_benefit_income

    date_range = generate_date_range(start, end)
    result = generate_yearly_income_per_month(date_range, total_gross_income)
    return result


estimate_yearly_income = {
    "1.0.0": estimate_yearly_income_100,
    "2.0.0": estimate_yearly_income_200,
}

def estimate_yearly_income_overtime(version: str, **args) -> dict[str, dict[str, float]]:
    assert (callback := estimate_yearly_income.get(version, None)) is not None, f"Invalid version number {version}"
    result = callback(**args)
    return result

def load_income_estimation_configuration(filepath: str) -> list[dict[str, str | float]]:
    gross_income_estimation_configuration = []
    with open(filepath, "r") as stream:
        data = toml.load(stream)
        for config in data["income_estimation"]:
            if config["version"] == "1.0.0":
                start = datetime.strptime(config["start"], "%Y-%d-%m")
                end = datetime.strptime(config["end"], "%Y-%d-%m")
                gross_income_estimation_configuration.append({
                    "version": config["version"],
                    "start": start,
                    "end": end,
                    "monthly_gross_salary_income": config["monthly_gross_salary_income"],
                    "monthly_gross_food_income": config["monthly_gross_food_income"],
                })
            elif config["version"] == "2.0.0":
                start = datetime.strptime(config["start"], "%Y-%d-%m")
                end = datetime.strptime(config["end"], "%Y-%d-%m") if config["end"] != "today" else datetime.today()
                gross_income_estimation_configuration.append({
                    "version": config["version"],
                    "start": start,
                    "end": end,
                    "monthly_gross_salary_income": config["monthly_gross_salary_income"],
                    "monthly_gross_food_income": config["monthly_gross_food_income"],
                    "monthly_benefit_income": config["monthly_benefit_income"]
                })
    return gross_income_estimation_configuration

if __name__ == "__main__":
    gross_income_estimation_configuration = load_income_estimation_configuration("././income_estimation_configuration.toml")

    result = {}
    for income_entry in gross_income_estimation_configuration:
        result.update(estimate_yearly_income_overtime(**income_entry))

    MONTHS_WORKED = 12
    WEEKS_WORKED = 4
    DAYS_WORKED = 5
    HOURS_WORKED = 8

