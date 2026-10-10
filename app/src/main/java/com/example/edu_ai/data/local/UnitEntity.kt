
// IDENTITY: data/local/UnitEntity.kt
// VERSION: 1.1.0
// ⚙️ GEAR 1.2: The Local Database (SQLite)
// This is our base currency. It handles the local ledger of all our data.

package com.example.edu_ai.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "units")
data class UnitEntity(
    @PrimaryKey(autoGenerate = true) val localId: Long = 0,
    val unitName: String,
    val isActive: Boolean,
    val cachedQuizJson: String? = null
)

val UnitEntity.exactFieldName: String
    get() = when {
        unitName.contains("Medicine", ignoreCase = true) ||
        unitName.contains("Surgery", ignoreCase = true) ||
        unitName.contains("Pharmacology", ignoreCase = true) ||
        unitName.contains("Obstetrics", ignoreCase = true) ||
        unitName.contains("Child Health", ignoreCase = true) ||
        unitName.contains("BCM", ignoreCase = true) ||
        unitName.contains("Emergency", ignoreCase = true) ||
        unitName.contains("Biochemistry", ignoreCase = true) -> "Clinical Medicine"
        unitName.contains("Computer", ignoreCase = true) ||
        unitName.contains("Software", ignoreCase = true) ||
        unitName.contains("Algorithms", ignoreCase = true) ||
        unitName.contains("Machine Learning", ignoreCase = true) -> "Computer Science & IT"
        else -> "Global Studies & Core Foundations"
    }

val UnitEntity.exactCourseName: String
    get() = when (exactFieldName) {
        "Clinical Medicine" -> "MBChB"
        "Computer Science & IT" -> "BSc. Software Engineering"
        else -> "Common Core Curriculum"
    }

val UnitEntity.exactUnitGroupName: String
    get() = when {
        unitName.contains("Internal Medicine I:", ignoreCase = true) || unitName.contains("Internal Medicine I (", ignoreCase = true) ->
            "Internal Medicine I: Cardiopulmonary and Haematology"
        unitName.contains("Internal Medicine II:", ignoreCase = true) || unitName.contains("Internal Medicine II (", ignoreCase = true) ->
            "Internal Medicine II: Neurology, Nephrology and Endocrinology"
        unitName.contains("Internal Medicine III:", ignoreCase = true) || unitName.contains("Internal Medicine III (", ignoreCase = true) ->
            "Internal Medicine III: Gastroenterology, Infectious Diseases, Rheumatology and Oncology"
        unitName.contains("GENERAL SURGERY I", ignoreCase = true) || unitName.equals("General Surgery", ignoreCase = true) ->
            "General Surgery I - BCM 314 - Principles, Emergency, GI Tract and Hernias"
        unitName.contains("GENERAL SURGERY II", ignoreCase = true) ->
            "General Surgery II - BCM 322 - Hepatobiliary, Urology, Breast, Vascular and Specialty Surgery"
        unitName.contains("Obstetrics and Gynaecology I", ignoreCase = true) ->
            "Obstetrics and Gynaecology I - BCM 317"
        unitName.contains("Obstetrics and Gynaecology II", ignoreCase = true) ->
            "Obstetrics and Gynaecology II - BCM 323 - Pathology and Management"
        unitName.contains("Clinical Pharmacology I:", ignoreCase = true) ->
            "Clinical Pharmacology I: Autonomic, Cardiovascular, Respiratory"
        unitName.contains("Clinical Pharmacology II:", ignoreCase = true) ->
            "Clinical Pharmacology II: Antimicrobials, CNS, Endocrine"
        unitName.contains("Clinical Pharmacology III", ignoreCase = true) ->
            "Clinical Pharmacology III - BCM 331"
        unitName.contains("General Pharmacology", ignoreCase = true) ->
            "General Pharmacology"
        unitName.contains("Emergency Medicine", ignoreCase = true) ->
            "Emergency Medicine and Life Support [ATLS & ACLS]"
        unitName.contains("Child Health", ignoreCase = true) ->
            "Child Health - BCM 312"
        unitName.contains("Research Methodology - HRS", ignoreCase = true) ->
            "Medical Research Methodology - HRS 312"
        unitName.contains("PHILOSOPHY", ignoreCase = true) ->
            "Introduction to Philosophy - EEN 114"
        unitName.contains("ENTREPRENEURSHIP", ignoreCase = true) ->
            "Entrepreneurship - HSN 425"
        unitName.contains("BASIC COMPUTER SKILLS", ignoreCase = true) || unitName.contains("Computer Skills", ignoreCase = true) ->
            "Basic Computer Skills - BCM 111"
        unitName.contains("RESEARCH METHODOLOGY", ignoreCase = true) ->
            "Research Methodology"
        else -> unitName
    }


 