# simple_simplex

> A lightweight Python package for solving linear programming problems using the simplex method.

## 🚀 Overview

**`simple_simplex`** is a minimal, NumPy-based Simplex solver that provides an easy interface for defining linear programs and solving them. It supports both maximization and minimization problems and includes features for logging pivot steps and returning results in JSON-friendly format — making it ideal for integration with web backends, educational tools, or visualization apps.

---

## 📦 Features

- 🧮 Solve both **maximization** and **minimization** problems  
- ✅ Support for **≤** and **≥** constraints  
- 📊 **Pivot step tracking** for visualization/debugging  
- 🔗 Returns results as **JSON-compatible dicts**  
- 📝 Display results as a neatly-formatted ASCII table
- 🧩 Easy to embed in Flask or FastAPI backends  

---

## 📥 Installation

```bash
pip install simple_simplex
```

---

## 🛠 Usage

### 1. Create a tableau

Pass in the number of variables, and number of constraints in the problem.

```python
from simple_simplex import *

tableau = create_tableau(number_of_variables=2, number_of_constraints=2)
```

### 2. Add constraints

Each constraint is passed as a string in the format:

```
"coeff1,coeff2,...,<inequality>,rhs"
```

Example:

```python
add_constraint(tableau, "2,1,L,18")  # 2x + y ≤ 18
add_constraint(tableau, "2,3,L,42")  # 2x + 3y ≤ 42
```

Use `"L"` for ≤, `"G"` for ≥

### 3. Add objective function

Objective format: `"coeff1,coeff2,...,objective"`  
(Set objective value to 0)

```python
add_objective(tableau, "3,2,0")  # Maximize 3x + 2y = z
```

### 4. Solve

#### Option 1 (print results, no return value)

```python
optimize_max(tableau) #prints results to stdout
```

```python
optimize_min(tableau) #prints results to stdout
```

#### Option 2 (generate and return JSON-compatible results)

_See Output Format for more details_

```python
result = optimize_json_format(tableau, maximize=True)
print(result["optimalValue"])       # => Optimal Z value
print(result["solutionValues"])     # => Variable values
print(result["pivotSteps"])         # => Step-by-step history
# See Output Format for more details
```

---

## 📄 Output Format

The `optimize_json_format()` function returns a Python dictionary in the form of:

```json
{
  "status": "optimal",
  "objectiveType": "max",
  "optimalValue": 36.0,
  "solutionValues": {
    "x1": 6.0,
    "x2": 6.0
  },
  "pivotSteps": [...],
  "finalTableau": [...],
  "numSteps": 2
}
```

The `optimize_max()` and `optimize_min()` functions display results as well as
the final tableau.

---

## 📚 Example Problem

**Maximize**:  
`Z = 3x + 2y`

**Subject to**:  

```
2x + y   ≤ 18  
2x + 3y  ≤ 42  
x, y ≥ 0
```

```python
from simple_simplex import *

tableau = create_tableau(2, 2)
add_constraint(tableau, "2,1,L,18")
add_constraint(tableau, "2,3,L,42")
add_objective(tableau, "3,2,0")

solution_dict = optimize_json_format(tableau, maximize=True)
# OR to print solution to stdout
optimize_max(tableau)
```

---

## 📏 To-Do

- Better input handling
- Better error handling

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

---

## 👤 Author

**Joshua Emralino**  
[jemralino@student.sdccd.edu](mailto:jemralino@student.sdccd.edu)

---

## 🌐 Keywords

`simplex`, `linear programming`, `optimization`, `math`, `solver`, `numpy`, `backend`, `json`, `flask`
