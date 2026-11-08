from rdflib import Namespace

SCHED = Namespace("http://example.org/schedule#")

PROJECT = SCHED.Project
ACTIVITY = SCHED.Activity
INCOMPLETE_ACTIVITY = SCHED.IncompleteActivity
POSITIVE_DURATION_ACTIVITY = SCHED.PositiveDurationActivity
RELATIONSHIP = SCHED.Relationship
CHECK = SCHED.Check
FINDING = SCHED.Finding
AUDIT_REPORT = SCHED.AuditReport

PROJECT_NAME = SCHED.projectName
DATA_DATE = SCHED.dataDate

ACTIVITY_ID = SCHED.activityId
ACTIVITY_NAME = SCHED.activityName
ACTIVITY_TYPE = SCHED.activityType
STATUS = SCHED.status
DURATION = SCHED.duration
START_DATE = SCHED.start
FINISH_DATE = SCHED.finish
ACTUAL_START = SCHED.actualStart
ACTUAL_FINISH = SCHED.actualFinish
TOTAL_FLOAT = SCHED.totalFloat
CONSTRAINT_TYPE = SCHED.constraintType
BASELINE_FINISH = SCHED.baselineFinish
RESOURCE = SCHED.resource

PREDECESSOR = SCHED.predecessor
SUCCESSOR = SCHED.successor
RELATIONSHIP_TYPE = SCHED.relationshipType
LAG = SCHED.lag
