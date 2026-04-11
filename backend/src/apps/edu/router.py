"""SavvyEdu app router — assembles all edu sub-module routers."""

from fastapi import APIRouter

from src.apps.edu.config.router import router as config_router
from src.apps.edu.structure.router import router as structure_router
from src.apps.edu.students.router import router as students_router
from src.apps.edu.teachers.router import router as teachers_router
from src.apps.edu.enrollment.router import router as enrollment_router
from src.apps.edu.scheduling.router import router as scheduling_router
from src.apps.edu.attendance.router import router as attendance_router
from src.apps.edu.grading.router import router as grading_router
from src.apps.edu.finance.router import router as finance_router
from src.apps.edu.documents.router import router as documents_router

router = APIRouter(prefix="/edu", tags=["SavvyEdu"])

router.include_router(config_router)
router.include_router(structure_router)
router.include_router(students_router)
router.include_router(teachers_router)
router.include_router(enrollment_router)
router.include_router(scheduling_router)
router.include_router(attendance_router)
router.include_router(grading_router)
router.include_router(finance_router)
router.include_router(documents_router)
