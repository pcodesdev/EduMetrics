# EduMetrics — Data Format Guide

## Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | UTF-8 encoded, comma-delimited |
| Excel | `.xlsx`, `.xls` | Auto-detects sheets; first sheet used by default |
| OpenDocument | `.ods` | LibreOffice / Google Sheets export |

## Required Columns

Your file **must** contain at least these two columns (names are flexible; the system auto-detects aliases):

| Field | Accepted Names | Example |
|-------|---------------|---------|
| Student Name | `student_name`, `name`, `student`, `pupil_name` | Amina Hassan |
| Student ID | `student_id`, `id`, `admission_no`, `adm_no`, `reg_no` | STU-001 |

## Optional Columns

More columns unlock richer analysis. Include as many as possible:

| Field | Accepted Names | Example | Used For |
|-------|---------------|---------|----------|
| Class | `class`, `grade`, `stream`, `form` | 8A | Class-level reports, gap analysis |
| Gender | `gender`, `sex` | Female | Gender gap analysis |
| Region | `region`, `county`, `district`, `zone` | Nairobi | Regional gap analysis |
| Term | `term`, `semester`, `period` | Term 1 | Trend analysis |
| Year | `year`, `academic_year` | 2025 | Multi-year trends |
| Subject scores | `math`, `mathematics`, `english`, `science`, `kiswahili`, `social_studies`, etc. | 78 | Subject analysis, rankings |

## Data Formats

### Wide Format (Recommended)
One row per student-term, subject scores as separate columns:

```csv
student_id,student_name,class,gender,term,math,english,science,kiswahili,social_studies
STU-001,Amina Hassan,8A,Female,Term 1,78,85,62,90,71
STU-002,Brian Kiptoo,8A,Male,Term 1,55,48,61,52,44
STU-003,Cynthia Wanjiku,8B,Female,Term 1,92,88,95,86,90
```

### Long Format
The system also accepts data in long format (one row per student-subject):

```csv
student_id,student_name,class,subject,score,term
STU-001,Amina Hassan,8A,math,78,Term 1
STU-001,Amina Hassan,8A,english,85,Term 1
STU-001,Amina Hassan,8A,science,62,Term 1
```

> The parser auto-detects layout. Wide format is preferred for simplicity.

## Score Values

- Scores should be **numeric** (integers or decimals)
- Expected range: **0–100** (percentage scale)
- Scores outside 0–100 are flagged as outliers during cleaning
- Missing scores are treated as absent and excluded from averages

## Tips

1. **Consistent naming**: Keep column headers lowercase and use underscores (e.g., `student_name`)
2. **No merged cells**: Avoid merged cells in Excel files
3. **Remove summary rows**: Delete any total/average rows at the bottom
4. **One dataset per file**: Don't mix different schools or datasets in one file
5. **UTF-8 encoding**: Save CSV files with UTF-8 encoding for special characters
