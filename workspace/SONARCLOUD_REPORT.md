# SonarCloud Code Quality Report

**Project:** Strangemother_python-hyperway
**Organization:** strangemother
**Generated:** 2025-10-19 15:32:41 UTC

---

## 📊 Quality Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Coverage** | 100.0% | ✅ |
| **Bugs** | 0 | ✅ |
| **Vulnerabilities** | 0 | ✅ |
| **Code Smells** | 28 | ⚠️ |
| **Duplicated Lines** | 0.0% | ✅ |
| **Technical Debt** | 2.6h | ℹ️ |
| **Lines of Code** | 822 | ℹ️ |
| **Complexity** | 246 | ℹ️ |

### Quality Ratings

| Category | Rating |
|----------|--------|
| **Reliability** | A 🟢 |
| **Security** | A 🟢 |
| **Maintainability** | A 🟢 |

---

## 🐛 Issues Summary

- **Total Issues:** 137
- **Bugs:** 5
- **Vulnerabilities:** 0
- **Code Smells:** 132

---

## 🐛 Bugs (5)

**Files Affected:** 4

### 📁 `tests/test_condition.py`

**Issues:** 2

- 🟡 **Line N/A:** Do not perform equality checks with floating point values.
  - *Rule:* `python:S1244`

- 🟡 **Line N/A:** Do not perform equality checks with floating point values.
  - *Rule:* `python:S1244`

### 📁 `tests/test_stepper_advanced.py`

**Issues:** 1

- 🟠 **Line N/A:** Change this assertion to not compare dissimilar types.
  - *Rule:* `python:S5845`

### 📁 `tests/test_stepper.py`

**Issues:** 1

- 🟡 **Line N/A:** The length of a collection is always ">=0", so update this test to either "==0" or ">0".
  - *Rule:* `python:S3981`

### 📁 `workspace/run.py`

**Issues:** 1

- 🟡 **Line N/A:** Delete this unreachable code or refactor the code to make it reachable.
  - *Rule:* `python:S1763`

---

## 🔒 Vulnerabilities

✅ **No vulnerabilities found!**

---

## 🔧 Code Smells (132)

**Files Affected:** 36

### Top 10 Files with Most Code Smells

#### 📁 `workspace/run.py` (11 issues)

<details>
<summary>View Issues</summary>

**🟠 CRITICAL** (1)

- Line N/A: Define a constant instead of duplicating this literal 'mul_.5' 3 times.
  - *Rule:* `python:S1192`

**🟡 MAJOR** (3)

- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`

**🔵 MINOR** (7)

- Line N/A: Remove the unused local variable "cs2".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "cs3".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "cs5".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "cd".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "cb".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "cc".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "cr".
  - *Rule:* `python:S1481`

</details>

#### 📁 `src/hyperway/stepper.py` (10 issues)

<details>
<summary>View Issues</summary>

**🟡 MAJOR** (10)

- Line 99: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 150: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 194: Replace this generic exception class with a more specific one.
  - *Rule:* `python:S112`
- Line 201: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 305: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 314: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 364: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 372: Remove the unused function parameter "thing".
  - *Rule:* `python:S1172`
- Line 400: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 428: Remove this commented out code.
  - *Rule:* `python:S125`

</details>

#### 📁 `tests/test_tools.py` (8 issues)

<details>
<summary>View Issues</summary>

**🟡 MAJOR** (8)

- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`

</details>

#### 📁 `tests/test_wire_func.py` (8 issues)

<details>
<summary>View Issues</summary>

**🟡 MAJOR** (8)

- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`

</details>

#### 📁 `src/hyperway/edges.py` (8 issues)

<details>
<summary>View Issues</summary>

**🟡 MAJOR** (5)

- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 99: Remove the unused function parameter "meta".
  - *Rule:* `python:S1172`
- Line 110: Remove the unused function parameter "meta".
  - *Rule:* `python:S1172`
- Line 232: Remove the unused function parameter "meta".
  - *Rule:* `python:S1172`

**🔵 MINOR** (3)

- Line N/A: Remove the unused local variable "g".
  - *Rule:* `python:S1481`
- Line 90: Remove the unused local variable "g".
  - *Rule:* `python:S1481`
- Line 250: Remove the unused local variable "g".
  - *Rule:* `python:S1481`

</details>

#### 📁 `src/hyperway/reader.py` (6 issues)

<details>
<summary>View Issues</summary>

**🟡 MAJOR** (5)

- Line 8: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 20: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 131: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 138: Remove this commented out code.
  - *Rule:* `python:S125`
- Line 147: Remove this commented out code.
  - *Rule:* `python:S125`

**🔵 MINOR** (1)

- Line 19: Replace this constructor call with a literal.
  - *Rule:* `python:S7498`

</details>

#### 📁 `tests/test_stepper_advanced.py` (5 issues)

<details>
<summary>View Issues</summary>

**🟡 MAJOR** (1)

- Line N/A: Update this function so that its implementation is not identical to test_call_one_fallthrough_2 on line 324.
  - *Rule:* `python:S4144`

**🔵 MINOR** (4)

- Line N/A: Replace the unused local variable "result" with "_".
  - *Rule:* `python:S1481`
- Line N/A: Consider using "assertIsNone" instead.
  - *Rule:* `python:S5906`
- Line N/A: Consider using "assertIsNone" instead.
  - *Rule:* `python:S5906`
- Line N/A: Consider using "assertIsNone" instead.
  - *Rule:* `python:S5906`

</details>

#### 📁 `tests/test_stepper.py` (5 issues)

<details>
<summary>View Issues</summary>

**🔵 MINOR** (5)

- Line N/A: Remove the unused local variable "e1".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "e2".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "e".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "e2".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "step2_result".
  - *Rule:* `python:S1481`

</details>

#### 📁 `workspace/hyperedge.py` (5 issues)

<details>
<summary>View Issues</summary>

**🟡 MAJOR** (4)

- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`

**🔵 MINOR** (1)

- Line N/A: Remove the unused local variable "cs2".
  - *Rule:* `python:S1481`

</details>

#### 📁 `workspace/arrows.py` (5 issues)

<details>
<summary>View Issues</summary>

**🟡 MAJOR** (3)

- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`
- Line N/A: Remove this commented out code.
  - *Rule:* `python:S125`

**🔵 MINOR** (2)

- Line N/A: Remove the unused local variable "sum_node".
  - *Rule:* `python:S1481`
- Line N/A: Remove the unused local variable "u".
  - *Rule:* `python:S1481`

</details>

*...and 26 more files*

---

## 📚 Resources

- [View on SonarCloud](https://sonarcloud.io/dashboard?id=Strangemother_python-hyperway)
- [Project Issues](https://sonarcloud.io/project/issues?id=Strangemother_python-hyperway)
- [Code Coverage](https://sonarcloud.io/component_measures?id=Strangemother_python-hyperway&metric=coverage)

---

*Report generated automatically from SonarCloud API*