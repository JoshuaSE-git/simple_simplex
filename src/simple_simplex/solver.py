import numpy as np
from ._typing import FloatTableau, FloatVector
from prettytable import PrettyTable


def create_tableau(
    number_of_variables: int, number_of_constraints: int
) -> FloatTableau:
    """
    Generates an empty simplex tableau based on number of variables and
    constraints.

    Parameters:
        number_of_variables (int): The number of variables in the problem.
        number_of_constraints (int): The number of constraints in the problem.

    Returns:
        FloatTableau: An empty initial tableau for the simplex problem.
    """
    tableau: FloatTableau = np.zeros(
        (number_of_constraints + 1, number_of_variables + number_of_constraints + 2)
    )
    return tableau


def add_constraint(tableau: FloatTableau, equation: str) -> None:
    """
    Adds a linear constraint to the simplex tableau.

    Parameters:
        tableau (FloatTableau): The simplex tableau.
        equation (str): String representation of the linear constraint.

    Returns:
        None: This function modifies the input tableau in place.

    Raises:
        ValueError: If there are no more empty rows in the tableau.
    """
    empty_rows: list[FloatVector] = list(
        filter(lambda row: sum(row) == 0, tableau[:-1])
    )
    if len(empty_rows) == 0:
        raise ValueError("Cannot add another constraint.")

    empty_index: int = 0
    while not np.array_equal(empty_rows[0], tableau[empty_index]):
        empty_index += 1
    empty_row: FloatVector = tableau[empty_index, :]

    equation_elements: list[float] = _parse_constraint(equation)
    element_index: int = 0
    while element_index < len(equation_elements) - 1:
        empty_row[element_index] = equation_elements[element_index]
        element_index += 1
    empty_row[-1] = equation_elements[-1]
    empty_row[_get_variable_count(tableau) + empty_index] = 1


def add_objective(tableau: FloatTableau, equation: str) -> None:
    """
    Adds an objective equation to the simplex tableau.

    Parameters:
        tableau (FloatTableau): The simplex tableau.
        equation (str): String representation of the objective equation.

    Returns:
        None: This function modifies the input tableau in place.

    Raises:
        ValueError: If there is not exactly one empty row in the tableau.
    """
    if not _has_empty_objective_row(tableau):
        raise ValueError("Must have exactly one empty row in the tableau")

    obj_equation_elements: list[float] = [float(coeff) for coeff in equation.split(",")]
    objective_row: FloatVector = tableau[len(tableau[:, 0]) - 1, :]

    objective_row_index = 0
    while objective_row_index < len(obj_equation_elements) - 1:
        objective_row[objective_row_index] = (
            obj_equation_elements[objective_row_index] * -1
        )
        objective_row_index += 1
    objective_row[-2] = 1
    objective_row[-1] = obj_equation_elements[-1]


def print_tableau(tableau: FloatTableau) -> None:
    """
    Takes in a FloatTableau and prints its contents as a formatted table.

    Parameters:
        tableau (FloatTableau): The simplex tableau to be printed.

    Returns:
        None: This function prints a visualization of the input tableau.
    """
    table: PrettyTable = PrettyTable()
    variable_names: list[str] = _make_var_names(tableau) + _make_slack_names(tableau)
    table.field_names = variable_names + ["Z", "RHS"]

    for row in tableau:
        table.add_row([f"{v:.2f}" for v in row])

    print(table)


def optimize_json_format(tableau: FloatTableau, maximize: bool = True) -> dict:
    """
    Solves the linear programming problem using the Simplex method and returns a JSON-compatible result.

    Parameters:
        tableau (FloatTableau): The initial simplex tableau.
        maximize (bool): Whether the objective is a maximization (default True).

    Returns:
        dict: A dictionary containing the optimal value, solution values, tableau steps, and metadata.
    """
    current_tableau: FloatTableau = tableau.copy()
    if not maximize:
        current_tableau: FloatTableau = _convert_min_to_max(current_tableau)

    while _is_infeasible(current_tableau):
        pivot_row, pivot_column = _select_infeasible_pivot(current_tableau)
        current_tableau: FloatTableau = _apply_pivot(
            pivot_row, pivot_column, current_tableau
        )

    step_count: int = 0
    pivot_steps: list[dict] = []
    _log_pivot_step(current_tableau, (None, None), step_count, pivot_steps)
    while _can_optimize(current_tableau):
        pivot_row, pivot_column = _select_pivot(current_tableau)
        current_tableau: FloatTableau = _apply_pivot(
            pivot_row, pivot_column, current_tableau
        )
        step_count += 1
        _log_pivot_step(
            current_tableau, (pivot_row, pivot_column), step_count, pivot_steps
        )

    return _format_json_output(current_tableau, step_count, pivot_steps, maximize)


def optimize_max(tableau: FloatTableau) -> None:
    """
    Maximizes the linear programming problem using the Simplex method and prints the results.

    Parameters:
        tableau (FloatTableau): The initial simplex tableau.

    Returns:
        None: The function prints the results of the maximization.
    """
    _optimize(tableau, maximize=True)


def optimize_min(tableau: FloatTableau) -> None:
    """
    Minimizes the linear programming problem using the Simplex method and prints the results.

    Parameters:
        tableau (FloatTableau): The initial simplex tableau.

    Returns:
        None: The function prints the results of the minimization.
    """
    _optimize(tableau, maximize=False)


def _is_infeasible(tableau: FloatTableau) -> bool:
    minimum: np.float64 = min(tableau[:-1, -1])
    if minimum >= 0:
        return False
    else:
        return True


def _can_optimize(tableau: FloatTableau) -> bool:
    number_of_rows: int = len(tableau[:, 0])
    last_row: int = number_of_rows - 1
    minimum: np.float64 = min(tableau[last_row, :-1])
    if minimum >= 0:
        return False
    else:
        return True


def _get_infeasible_row_index(tableau: FloatTableau) -> int:
    rhs_column: FloatVector = tableau[:-1, -1]
    rhs_minimum: np.float64 = min(rhs_column)
    if rhs_minimum > 0:
        raise ArithmeticError("Cannot optimize further.")
    infeasible_row_index: int = np.where(rhs_column == rhs_minimum)[0][0]
    return infeasible_row_index


def _get_pivot_col_index(tableau: FloatTableau) -> int:
    objective_row: FloatVector = tableau[-1, :-1]
    objective_row_minimum: np.float64 = min(objective_row)
    if objective_row_minimum > 0:
        raise ArithmeticError("Cannot optimize further.")
    pivot_column_index: int = int(
        np.where(objective_row == objective_row_minimum)[0][0]
    )
    return pivot_column_index


def _select_infeasible_pivot(tableau: FloatTableau) -> tuple[int, int]:
    ratios = []
    infeasible_row: FloatVector = tableau[_get_infeasible_row_index(tableau), :-1]
    pivot_column_index: int = np.where(infeasible_row == min(infeasible_row))[0][0]
    pivot_column: FloatVector = tableau[:-1, pivot_column_index]
    for a, b in zip(pivot_column, tableau[:-1, -1]):
        if a**2 > 0 and b / a > 0:
            ratios.append(b / a)
        else:
            ratios.append(float("inf"))
    pivot_row_index = ratios.index(min(ratios))
    return (pivot_row_index, pivot_column_index)


def _select_pivot(tableau: FloatTableau) -> tuple[int, int]:
    if not _can_optimize(tableau):
        raise ArithmeticError("Cannot pivot.")

    ratios = []
    pivot_column_index: int = _get_pivot_col_index(tableau)
    pivot_column: FloatVector = tableau[:-1, pivot_column_index]
    rhs_column: FloatVector = tableau[:-1, -1]
    for column_value, rhs_value in zip(pivot_column, rhs_column):
        if column_value**2 > 0 and rhs_value / column_value > 0:
            ratios.append(rhs_value / column_value)
        else:
            ratios.append(float("inf"))
    pivot_row_index: int = ratios.index(min(ratios))
    return (pivot_row_index, pivot_column_index)


def _apply_pivot(
    pivot_row_index: int, pivot_column_index: int, tableau: FloatTableau
) -> FloatTableau:
    number_of_rows = len(tableau[:, 0])
    number_of_columns = len(tableau[0, :])
    new_tableau = np.zeros((number_of_rows, number_of_columns))
    pivot_row: FloatVector = tableau[pivot_row_index, :]
    if tableau[pivot_row_index, pivot_column_index] ** 2 > 0:
        scalar = 1 / tableau[pivot_row_index, pivot_column_index]
        new_pivot_row: FloatVector = pivot_row * scalar
        for i in range(len(tableau[:, pivot_column_index])):
            k = tableau[i, :]
            c = tableau[i, pivot_column_index]
            if list(k) == list(pivot_row):
                continue
            else:
                new_tableau[i, :] = list(k - new_pivot_row * c)
        new_tableau[pivot_row_index, :] = list(new_pivot_row)
        return new_tableau
    else:
        raise ArithmeticError("Cannot pivot on this element.")


def _parse_constraint(equation) -> list[float]:
    equation = equation.split(",")
    if ("G" or "g") in equation:
        greater_symbol_index = equation.index("G")
        del equation[greater_symbol_index]
        equation = [float(coeff) * -1 for coeff in equation]
        return equation
    if ("L" or "l") in equation:
        less_symbol_index = equation.index("L")
        del equation[less_symbol_index]
        equation = [float(coeff) for coeff in equation]
        return equation
    raise ValueError("Cannot parse constraint. No inequality symbol.")


def _convert_min_to_max(tableau: FloatTableau) -> FloatTableau:
    tableau[-1, :-2] = [-1 * coeff for coeff in tableau[-1, :-2]]
    tableau[-1, -1] = -1 * tableau[-1, -1]
    return tableau


def _get_variable_count(tableau: FloatTableau) -> int:
    number_of_columns: int = len(tableau[0, :])
    number_of_rows: int = len(tableau[:, 0])
    number_of_variables: int = number_of_columns - number_of_rows - 1
    return number_of_variables


def _make_var_names(tableau: FloatTableau) -> list[str]:
    variables: list[str] = []
    for i in range(_get_variable_count(tableau)):
        variables.append("x" + str(i + 1))

    return variables


def _make_slack_names(tableau) -> list[str]:
    slacks = []
    number_of_constraints = len(tableau[:-1, 0])
    for i in range(number_of_constraints):
        slacks.append("s" + str(i + 1))
    return slacks


def _has_empty_objective_row(tableau: FloatTableau) -> bool:
    num_rows = len(tableau[:, 0])
    empty_count = 0
    for i in range(num_rows):
        total = 0
        for j in tableau[i, :]:
            total += j**2
        if total == 0:
            empty_count += 1
    return empty_count == 1


def _log_pivot_step(
    tableau: FloatTableau, pivots: tuple[int | None, int | None], step: int, log: list
):
    current_pivot = {}
    current_pivot["step"] = step
    current_pivot["pivotRowIndex"] = pivots[0]
    current_pivot["pivotColIndex"] = pivots[1]
    current_pivot["currentSolution"] = _get_current_solution(tableau)
    current_pivot["tableau"] = tableau.tolist()
    log.append(current_pivot)


def _get_current_solution(tableau: FloatTableau):
    solutions = {}
    variable_names = _make_var_names(tableau)
    for i in range(_get_variable_count(tableau)):
        current_column: FloatVector = tableau[:, i]
        max_column_value = max(current_column)
        if float(sum(current_column)) == float(max_column_value):
            basic_variable_index = np.where(current_column == max_column_value)[0][0]
            solutions[variable_names[i]] = float(tableau[basic_variable_index, -1])
        else:
            solutions[variable_names[i]] = 0
    return solutions


def _format_json_output(tableau, step_count, pivot_steps, maximize):
    solution = float(tableau[-1, -1])
    if not maximize:
        solution *= -1

    optimization_log = {
        "status": "optimal",
        "objectiveType": "max" if maximize else "min",
        "optimalValue": solution,
        "solutionValues": _get_current_solution(tableau),
        "pivotSteps": pivot_steps,
        "finalTableau": tableau.tolist(),
        "numSteps": step_count,
    }

    return optimization_log


def _optimize(tableau, maximize=True):
    current_tableau: FloatTableau = tableau.copy()
    if not maximize:
        current_tableau: FloatTableau = _convert_min_to_max(current_tableau)
    while _is_infeasible(current_tableau):
        pivot_row, pivot_column = _select_infeasible_pivot(current_tableau)
        current_tableau: FloatTableau = _apply_pivot(
            pivot_row, pivot_column, current_tableau
        )
    while _can_optimize(current_tableau):
        pivot_row, pivot_column = _select_pivot(current_tableau)
        current_tableau: FloatTableau = _apply_pivot(
            pivot_row, pivot_column, current_tableau
        )

    _display_final_results(current_tableau, maximize)


def _display_final_results(tableau: FloatTableau, maximize: bool) -> None:
    solution_vars = _get_current_solution(tableau)
    solution = float(tableau[-1, -1])
    if not maximize:
        solution *= -1

    variable_values: str = ""
    for variable, value in solution_vars.items():
        if len(variable_values) == 0:
            variable_values += f"{variable}: {value:.2f}"
        else:
            variable_values += f", {variable}: {value:.2f}"

    print(f"Optimal Value: {solution:.3f}")
    print(f"Solution Values: ({variable_values})")

    print("\nFinal Tableau")
    print_tableau(tableau)
