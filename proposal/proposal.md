# Schedule quality checker for construction programmes using DCMA checks and SHACL rules

SEN0414 Advanced Programming · 2026-2027 Fall · Proposal · Method: BRSF software-development profile · Self-assessed grade 96.7/100

## Team, roles and work distribution

| Member | Student number | E-mail | Administrative roles | Development roles | Planned share |
| --- | --- | --- | --- | --- | --- |
| Arda Özcan | 2200004482 | 2200004482@stu.iku.edu.tr | Team lead, Customer liaison | Requirements analyst, Back-end developer | 16% |
| Aysu Akdüzen | 2200004962 | 2200004962@stu.iku.edu.tr | Documentation lead | Back-end developer, Data engineer | 14% |
| Esra Kaya | 2200004278 | 2200004278@stu.iku.edu.tr | Work-log steward | Back-end developer | 14% |
| Eylem Sarıbal | 2000003742 | 2000003742@stu.iku.edu.tr | Quality lead | Knowledge engineer, Architect | 14% |
| Burak Sami Şirin | 2200004655 | 2200004655@stu.iku.edu.tr | Process facilitator | Knowledge engineer | 14% |
| Arda Çiftçi | 2300005868 | 2300005868@stu.iku.edu.tr | Repository and release manager | Knowledge engineer, Back-end developer | 14% |
| Mehmet Mert Seyhan | 2300007247 | 2300007247@stu.iku.edu.tr | Quality lead | Test engineer | 14% |

### Modules and features

| Module or feature | Kind | What it does | Delivers epic | Responsible member | Second member |
| --- | --- | --- | --- | --- | --- |
| Template reader | Module | Reads the three-sheet Excel template with openpyxl, checks the required columns and cleans values with regular expressions | Read the programme reliably | Aysu Akdüzen · 2200004962 | Esra Kaya · 2200004278 |
| Programme vocabulary and RDF mapping | Module | The small vocabulary for project, activity and relationship, and the mapping from template rows to RDF | Read the programme reliably | Eylem Sarıbal · 2000003742 | Burak Sami Şirin · 2200004655 |
| Logic and constraint shapes (checks 1-5) | Module | SHACL shapes for missing logic, leads, lags, relationship types and hard constraints, with their ratios | Check the programme against the DCMA rules | Burak Sami Şirin · 2200004655 | Eylem Sarıbal · 2000003742 |
| Float, date and resource shapes (checks 6-11, BEI) | Module | SHACL shapes for high and negative float, long durations, invalid dates, resources and missed activities, and the SPARQL query for the baseline execution index | Check the programme against the DCMA rules | Arda Çiftçi · 2300005868 | Burak Sami Şirin · 2200004655 |
| Excel audit report | Feature | The summary, findings and method sheets written with openpyxl, in the form the planning team asked for | Report the findings to the planning engineer | Arda Özcan · 2200004482 | Aysu Akdüzen · 2200004962 |
| Command line and folder mode | Feature | The command that checks one file or a whole folder, with pathlib and a thread pool, and the folder summary table | Report the findings to the planning engineer | Esra Kaya · 2200004278 | Arda Özcan · 2200004482 |
| Synthetic programmes and tests | Module | The generator of synthetic programmes with seeded defects and the pytest case for every story | Check the programme against the DCMA rules | Mehmet Mert Seyhan · 2300007247 | Arda Çiftçi · 2300005868 |

### Process leads

- Mission analysis: Arda Özcan
- Stakeholder needs and requirements: Arda Özcan
- System/software requirements definition: Aysu Akdüzen
- Architecture definition: Eylem Sarıbal
- Design definition: Eylem Sarıbal
- System analysis: Burak Sami Şirin
- Implementation: Esra Kaya
- Integration: Arda Çiftçi
- Verification: Mehmet Mert Seyhan
- Transition: Arda Çiftçi
- Validation: Arda Özcan
- Operation: Esra Kaya
- Maintenance: Arda Çiftçi
- Disposal: Mehmet Mert Seyhan

### Work log

0 entries; chain intact; head fingerprint none.

## 1. Mission

### Customer

| Customer (organisation or role) | Contact person or role | How and when you reached them | Relation | What they get from it |
| --- | --- | --- | --- | --- |
| Construction project management firm, planning and project controls team | Entegre Project Management: Kemal Okumuş, M.Sc. Civil Engineer, General Manager Yaren Yanbel, Technical Office Engineer Efe Mert İşgör, Civil Engineer Ayşe Yıldız Architect | Face-to-face meeting at the firm's office on 12 October 2026 | Client who orders it | A repeatable, documented quality check of every contractor programme in minutes, with a finding list it can send back to the contractor. |

### End users

| User group (short name) | Who exactly | What they do with the system | How often | Device or channel |
| --- | --- | --- | --- | --- |
| Planning engineer | planning engineers of the project management firm who review contractor programmes | exports the contractor's programme to the Excel template, runs the checker and reviews the findings before replying to the contractor | Monthly | office laptop |
| Project manager | project managers who accept or return a contractor's programme on behalf of the employer | reads the summary sheet of the report to decide whether the programme can be accepted | Monthly | office laptop |

### Problem

On every project the contractor submits an updated programme, a Primavera P6 or MS Project schedule, and a planning engineer of the project management firm has to review it before the project manager can accept it on the employer's behalf. Today this review is done by eye: the engineer filters the activity table, looks for activities without predecessors or successors, hard constraints, negative float and unexplained lags, and writes the comments into an e-mail or a spreadsheet by hand. The DCMA 14-point assessment is the common yardstick for schedule quality: for example, at most 5% of incomplete activities may miss a predecessor or successor, no link may have a negative lag, and at most 5% of activities may carry more than 44 working days of total float. Counting these by hand across a large programme is slow and error-prone, and two engineers rarely count the same way; even the commercial tools that automate the checks are not certified and count activities differently. When a defective programme is accepted, its critical path is wrong, and every later delay or extension-of-time discussion rests on a schedule nobody fully checked.

### Mission statement

Help the planning engineers of a construction project management firm review contractor programmes faster and more consistently. The project delivers a Python tool that reads a programme exported to Excel, checks it against twelve of the DCMA 14-point schedule quality checks written as SHACL rules, and produces an Excel report that lists every finding by activity. With this report, the planning engineer can send precise, rule-based comments to the contractor, and the project manager can accept a programme knowing that its logic, float and dates have been checked the same way every time.

Origin: Derived

### Outcome

A planning engineer runs one command on the contractor's exported programme and, within a minute, receives an Excel report with a pass or fail for twelve DCMA checks and a list of every offending activity, ready to send back to the contractor, instead of filtering the schedule by hand.

## 2. Scope

### Areas

| Area | Where it lives | How big it is today |
| --- | --- | --- |
| Template reading | reader/ | 0 programmes read automatically today |
| Programme graph and rules | graph/ and shapes/ | 0 checks written as rules today |
| Report and command line | report/ and cli/ | no generated report today |

### Deliverables

| Deliverable | Area | Layer | Kind |
| --- | --- | --- | --- |
| Excel template and reader with column checks and regular-expression value clean-up | Template reading | Product layer | Functional |
| Synthetic programme generator with seeded defects and automated tests | Template reading | Work layer | Non-functional |
| Programme vocabulary and Excel-to-RDF mapping | Programme graph and rules | Product layer | Functional |
| SHACL shapes for eleven checks and SPARQL queries for the ratios and the baseline execution index | Programme graph and rules | Product layer | Functional |
| A programme of 1,000 activities is checked in under 30 seconds | Programme graph and rules | Product layer | Non-functional |
| Excel audit report with summary, findings and method sheets | Report and command line | Product layer | Functional |
| Command-line tool that checks one file or a whole folder | Report and command line | Product layer | Functional |
| Every finding traces back to its rule and to its activity or link | Report and command line | Product layer | Non-functional |

### Exclusions

| Left out | Why |
| --- | --- |
| Recalculating the schedule (CPM), the critical path test and the critical path length index | they need the planning software's calculation engine; the values in the export are enough for the other twelve checks |
| Reading XER, MPP or MS Project XML files directly | each format needs its own parser, and both P6 and MS Project can export the activity table to Excel |
| Revision comparison, trend charts, a web interface and a database | checking one file at a time meets the need, and the tool is run by one engineer on one computer |
| Correcting the programme or writing back to it | the reviewer must stay independent; corrections are the contractor's job |
| Delay analysis and extension-of-time assessment | it needs expert and contractual judgement beyond rule checks |
| Real project programmes in the repository | programmes are confidential; the repository holds synthetic files only |

### Domain entities

| Entity | What it is | Created? | Used? | Retired? |
| --- | --- | --- | --- | --- |
| Project | the programme being checked, with its name and data date | Created — no | Used — yes | Retired — no |
| Activity | a work item with its type, status, duration, dates, total float, constraint and resource | Created — no | Used — yes | Retired — no |
| Relationship | a predecessor-successor link between two activities, with its type (FS, SS, FF, SF) and lag | Created — no | Used — yes | Retired — no |
| Check | one DCMA rule in the rules file, with its threshold and counting rule | Created — no | Used — yes | Retired — no |
| Finding | the result of one check for one activity or link, with the measured value and a message | Created — yes | Used — yes | Retired — no |

### Project kinds

Data quality and validation › Shape-based validation service. Stack layers they need: Engineering practice, Reasoning, Validation.

### Semantic technologies, by stack layer

- Data model: RDFLib
- Query: SPARQL 1.1 and 1.2
- Serialisation: RDFLib
- Validation: SHACL shapes, pySHACL

RDFLib turns the rows of the Excel template into RDF statements about the project, its activities and the relationships between them, so that each finding can point at the activity or link it concerns. SHACL shapes, run by pySHACL, hold the eleven rule-based DCMA checks; each threshold is a value in the shapes file, so a planning engineer can change it without touching code. SPARQL queries count the ratios each check is judged by and compute the baseline execution index for the report's summary sheet.

## 3. Goals

| Goal | Facing | Covers area | Why this goal |
| --- | --- | --- | --- |
| Defective programmes are caught before they are accepted | Mission-facing | Programme graph and rules | this is the change the planning team needs |
| Every template column the checks need is read reliably | Scope-facing | Template reading | a column read wrongly would hide or invent findings |
| The planning engineer receives a report ready to send to the contractor | Scope-facing | Report and command line | the check is only useful if its result reaches the contractor |
| No work is spent outside the three scope areas | Containment-facing | Programme graph and rules | recalculation, file parsers and a web interface were left out to keep the project small |

### Specification

The tool reads a programme from the three-sheet Excel template (Project, Activities, Relationships), refuses a file whose required columns are missing and names them, and converts each value, accepting forms such as 12, 12d or 12 gün. It maps the programme to an RDF graph and validates it with SHACL shapes for checks 1 to 11 of the DCMA 14-point assessment; SPARQL queries compute each check's ratio and the baseline execution index. It writes an Excel report with a summary sheet (value, threshold and pass, fail or not applicable per check), a findings sheet with one row per finding, and a method sheet with the counting rules. Given a folder, it checks every file in parallel and adds one summary table. It never recalculates the schedule and never sends data outside the computer.

### Test scenarios

| Kind | Scenario (Given / When / Then) |
| --- | --- |
| Nominal | Given a defect-free synthetic programme of 200 activities, when the planning engineer runs the checker, then all twelve checks pass and the findings sheet is empty |
| Rejection | Given a template whose Relationships sheet lacks the predecessor column, when the checker reads it, then it stops, names the missing column and writes no report |
| Boundary | Given an activity with exactly 44 working days of total float, when the checker runs, then check 6 reports no finding for it, and at 45 days it does |
| Absent | Given a programme with an empty baseline finish column, when the checker runs, then checks 11 and 14 are reported as not applicable rather than passed |

### Use cases

Planning engineer: export the programme to the template, check one file, check a folder, change a threshold. Project manager: read the summary sheet, accept or return the programme.

## 4. Objectives

| Objective | Goal | Measured by | How exactly it is measured | Now | Target | Direction |
| --- | --- | --- | --- | --- | --- | --- |
| Seeded defects detected | Defective programmes are caught before they are accepted | Counted | share of the defects seeded into the synthetic test programmes that appear in the findings sheet | 0% | 95% | Increase |
| Template columns read without manual editing | Every template column the checks need is read reliably | Counted | required template columns the reader accepts in the sample files, out of 19 | 0 | 19 | Increase |
| Report sheets produced automatically | The planning engineer receives a report ready to send to the contractor | Counted | sheets of the audit report (summary, findings, method) written by the tool without manual editing | 0 | 3 | Increase |
| Commits outside the scope areas | No work is spent outside the three scope areas | Derived | git log query counting commits that change files outside reader/, graph/, shapes/, report/, cli/ and tests/ | 0 | 0 | Hold |

### Activity model

The planning engineer exports the contractor's programme to the template and starts the checker on a file or a folder. For a folder, each file is processed in its own thread. The reader opens the workbook; if a required sheet or column is missing it stops and reports it. Otherwise it cleans each value, and an unreadable cell is reported with its sheet and row. The rows are mapped to an RDF graph. pySHACL validates the graph against the shapes and SPARQL queries compute the ratios and the baseline execution index; if the baseline column is empty, checks 11 and 14 are marked not applicable. The report writer produces the Excel report, and for a folder the summary table.

### Sequence model

The planning engineer calls the command-line tool with a path. The tool asks the Reader for the three sheets and receives rows or a list of missing columns. It sends the rows to the Mapper, which returns an RDF graph. It sends the graph and the shapes file to the Validator (pySHACL), which returns the validation report. It sends the graph to the Metrics module, which runs the SPARQL queries and returns one value per check. It passes the findings and values to the ReportWriter, which writes the Excel file and returns its path, and the tool prints the path for the engineer.

## 5. Backlog

Kind of development: Initial development

### Epics

| Epic | Pursues objective |
| --- | --- |
| Read the programme reliably | Template columns read without manual editing |
| Check the programme against the DCMA rules | Seeded defects detected |
| Report the findings to the planning engineer | Report sheets produced automatically |

### Stories

| Epic | As a | I want | So that | Acceptance (Given / When / Then) | Category | Design concern | Value 1–10 | Time 1–10 | Risk 1–10 | Size 1–10 | Priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Read the programme reliably | Planning engineer (end user) | to load a programme exported to the Excel template without editing it | I can check it as soon as the contractor sends it | Given a template with all required columns When I run the checker on it Then every activity and relationship is read and their counts appear in the report | New capability | Data | 8 | 6 | 5 | 5 | 3.8 |
| Read the programme reliably | Planning engineer (end user) | a clear message when a required column is missing or a cell cannot be read | I fix the export instead of trusting a wrong result | Given a template without the predecessor column When I run the checker Then it stops, names the missing column and writes no report | New capability | Interface | 6 | 4 | 7 | 2 | 8.5 |
| Check the programme against the DCMA rules | Planning engineer (end user) | the logic checks (missing links, leads, lags, relationship types) applied to every activity | I see where the network is broken | Given a programme with one activity missing its successor and one link with a negative lag When I run the checker Then checks 1 and 2 fail and list exactly those two items | New capability | Data | 9 | 7 | 6 | 5 | 4.4 |
| Check the programme against the DCMA rules | Planning engineer (end user) | the float, duration, constraint, date and resource checks applied | I see the activities that make the critical path unreliable | Given a programme with an activity of 61 days total float and one with a Must Finish On constraint When I run the checker Then checks 6 and 5 list those activities with their values | New capability | Data | 8 | 6 | 5 | 5 | 3.8 |
| Check the programme against the DCMA rules | Planning engineer (end user) | to change a threshold in the rules file | the checks follow our firm's own limits | Given the high-float threshold changed from 44 to 30 days When I run the checker on a programme with an activity of 35 days float Then check 6 lists that activity | New capability | Data | 5 | 3 | 4 | 3 | 4 |
| Report the findings to the planning engineer | Project manager (end user) | a summary sheet with a pass or fail per check | I can decide whether to accept the programme | Given a checked programme When I open the report Then the summary sheet shows each check with its value, threshold and pass, fail or not applicable | New capability | Interaction | 8 | 6 | 4 | 3 | 6 |
| Report the findings to the planning engineer | Planning engineer (end user) | to check every programme in a folder at once | I can review all projects' updates in one run | Given a folder with three templates When I run the checker on the folder Then each file gets its own report and one summary table lists all three | New capability | Interaction | 5 | 4 | 3 | 4 | 3 |

### Definition of done

| Criterion | How it is checked |
| --- | --- |
| All tests pass in continuous integration | GitHub Actions run on every push |
| The story's acceptance criterion has a passing test | a pytest test named after the story id |
| The sample graph conforms to the shapes and the report opens in Excel | pySHACL report in the test log and a sample report attached to the release |

### Class model

Project has a name and a data date and has many Activities. Activity has an id, name, type (task, milestone, level of effort, summary), status, duration, start, finish, actual start, actual finish, total float, constraint type, baseline finish and resource. Relationship links a predecessor Activity to a successor Activity and has a type (FS, SS, FF, SF) and a lag. Check has a number, a name, a threshold and a counting rule. Finding links one Check to one Activity or Relationship and has a measured value and a message. AuditReport belongs to one Project and holds a result per Check and many Findings.

### Test cases

| For story | Test case | Test data |
| --- | --- | --- |
| to load a programme exported to the Excel template without editing it | read a 200-activity synthetic template and compare the counts with the generator's | synthetic template from the test-data generator |
| a clear message when a required column is missing or a cell cannot be read | remove the predecessor column and expect a stop that names it | synthetic template with one column removed |
| the logic checks (missing links, leads, lags, relationship types) applied to every activity | seed one missing successor and one negative lag and expect exactly two findings in checks 1 and 2 | synthetic programme with two seeded defects |
| the float, duration, constraint, date and resource checks applied | seed 61 days of float and a Must Finish On constraint and expect findings in checks 6 and 5 | synthetic programme with two seeded defects |
| to change a threshold in the rules file | lower the float threshold to 30 days and expect a 35-day activity to be listed | rules file with a changed threshold and a small programme |
| a summary sheet with a pass or fail per check | compare the summary sheet with the expected pass, fail or not applicable per check | synthetic programme with known results |
| to check every programme in a folder at once | run on a folder of three templates and expect three reports and one summary table | three small synthetic templates |

### Data — Class diagram

Class diagram: Project, Activity, Relationship, Check, Finding and AuditReport as in the class model. SHACL node shapes target Activity and Relationship, one shape per check, each with its threshold as a parameter and a message for the report.

### Interaction — Sequence diagram

Sequence diagram: the planning engineer runs the command with a file or folder path; the tool prints progress per file and then the report path, or the missing column and stops; the project manager opens the report and reads the summary sheet.

### Interface — Component diagram

Component diagram: the CLI calls the Reader (openpyxl, re), which feeds the Mapper (RDFLib); the Validator (pySHACL) reads the graph and the shapes file; Metrics runs the SPARQL queries; the ReportWriter (openpyxl) writes the Excel report. The file contracts are the three-sheet input template and the three-sheet report.

## 6. Course-specific

### Python libraries and course topics

openpyxl reads the Excel template and writes the audit report, regular expressions clean values such as 12d or 12 gün and check activity id patterns, pathlib walks a folder of programmes and stores the reports, and a thread pool checks several files in parallel. RDFLib builds the graph, pySHACL validates it against the shapes and pytest runs the tests. The project applies the course's spreadsheet, regular expressions, files and paths, and multithreading chapters.

## Plan and risks

| Date | Deliverable | Lead |
| --- | --- | --- |
| 2026-10-30 | Proposal submitted; Excel template and synthetic programme generator agreed | Arda Özcan |
| 2026-11-13 | Template reader and Excel-to-RDF mapping with tests | Aysu Akdüzen |
| 2026-11-27 | SHACL shapes and SPARQL queries for the twelve checks | Burak Sami Şirin |
| 2026-12-11 | Excel report, folder mode and validation with the planning team | Arda Özcan |
| 2026-12-18 | Tagged release v1.0 with test report | Arda Çiftçi |

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| The firm's planners cannot export programmes in the template's columns | Medium | High | agree the template with the planning team in the first week and accept common column-name variants |
| Real programmes are confidential and cannot be used for testing | High | Medium | build the synthetic programme generator first; use one anonymised programme only for validation, never in the repository |
| Values in the export are stale because the schedule was not recalculated before export | Medium | Medium | show the data date on the summary sheet and state in the method sheet that values are taken as exported |
| Learning SHACL takes longer than planned | Medium | Medium | write the first two shapes in the first week as a spike and keep the other rules in the same form |

Repository: https://github.com/aozcan4482/schedule_quality_checker — Given, not yet confirmed

## References

1. Mosaic Project Services. WP1088: The DCMA 14-Point Schedule Assessment. https://mail.mosaicprojects.com.au/WhitePapers/WP1088_DCMA-14-Point.pdf
2. Deltek. Acumen 8.11: DCMA 14-Point Assessment Metric Descriptions. https://help.deltek.com/Product/Acumen/8.11/GA/DCMA%2014%20Point%20Assessment%20Metric%20Descriptions.html
3. W3C (2017). Shapes Constraint Language (SHACL). W3C Recommendation. https://www.w3.org/TR/shacl/
4. W3C (2013). SPARQL 1.1 Query Language. W3C Recommendation. https://www.w3.org/TR/sparql11-query/
5. RDFLib documentation. https://rdflib.readthedocs.io
6. pySHACL. https://github.com/RDFLib/pySHACL
7. Sweigart, A. (2025). Automate the Boring Stuff with Python, 3rd ed. No Starch Press.
8. Hagedorn, P., Cassandro, J., Sigalov, K., Mirarchi, C., Pavan, A., Koenig, M. (2025). Cost and resource ontologies for construction scheduling. LDAC 2025, Porto.

## Self-assessment

| Part | Weight | Grade | Criteria met |
| --- | --- | --- | --- |
| Team and work | 10% | 67/100 | 9 of 12 |
| Mission | 20% | 100/100 | 7 of 7 |
| Scope | 15% | 100/100 | 8 of 8 |
| Goal | 15% | 100/100 | 7 of 7 |
| Objective | 10% | 100/100 | 3 of 3 |
| Backlog | 20% | 100/100 | 10 of 10 |
| Course-specific | 5% | 100/100 | 1 of 1 |
| Plan and references | 5% | 100/100 | 3 of 3 |
| Overall | 100% | 96.7/100 |  |

### Member grades (Proposal)

Project grade 100 (60%), team grade 67 (20%), individual contribution (20%).

| Member | Student number | Individual | Member grade |
| --- | --- | --- | --- |
| Arda Özcan | 2200004482 | 22 | 77.8 |
| Aysu Akdüzen | 2200004962 | 22 | 77.8 |
| Esra Kaya | 2200004278 | 22 | 77.8 |
| Eylem Sarıbal | 2000003742 | 22 | 77.8 |
| Burak Sami Şirin | 2200004655 | 22 | 77.8 |
| Arda Çiftçi | 2300005868 | 22 | 77.8 |
| Mehmet Mert Seyhan | 2300007247 | 22 | 77.8 |

