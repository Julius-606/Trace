package com.example.edu_ai.ui.screens.student

import androidx.compose.animation.*
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.example.edu_ai.EduAIApplication
import com.example.edu_ai.data.remote.LibraryUnit
import com.example.edu_ai.ui.components.DynamicBackground
import com.example.edu_ai.utils.TactileFeedback

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LibraryScreen(
    userId: String,
    onBack: () -> Unit,
    onUnitAdded: () -> Unit
) {
    val context = LocalContext.current
    val app = context.applicationContext as EduAIApplication
    val viewModel: LibraryViewModel = viewModel(
        factory = LibraryViewModel.Factory(app.repository)
    )
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(Unit) {
        viewModel.loadLibrary()
    }

    // Curated fallback matching the 21 authentic units in the backend
    val fallbackUnits = remember {
        listOf(
            LibraryUnit(3, "Internal Medicine I: Cardiopulmonary and Haematology", "Clinical Medicine", "MBChB", "Internal Medicine I: Cardiopulmonary and Haematology"),
            LibraryUnit(1, "Internal Medicine I (Crash Course): Cardiopulmonary and Haematology", "Clinical Medicine", "MBChB", "Internal Medicine I: Cardiopulmonary and Haematology"),
            LibraryUnit(5, "Internal Medicine II: Neurology, Nephrology and Endocrinology", "Clinical Medicine", "MBChB", "Internal Medicine II: Neurology, Nephrology and Endocrinology"),
            LibraryUnit(4, "Internal Medicine II (Crash Course): Neurology, Nephrology and Endocrinology", "Clinical Medicine", "MBChB", "Internal Medicine II: Neurology, Nephrology and Endocrinology"),
            LibraryUnit(7, "Internal Medicine III: Gastroenterology, Infectious Diseases, Rheumatology and Oncology", "Clinical Medicine", "MBChB", "Internal Medicine III: Gastroenterology, Infectious Diseases, Rheumatology and Oncology"),
            LibraryUnit(6, "Internal Medicine III (Crash Course): Gastroenterology, Infectious Diseases, Rheumatology and Oncology", "Clinical Medicine", "MBChB", "Internal Medicine III: Gastroenterology, Infectious Diseases, Rheumatology and Oncology"),
            LibraryUnit(18, "GENERAL SURGERY I - BCM 314 - Principles, Emergency, GI Tract and Hernias", "Clinical Medicine", "MBChB", "General Surgery I - BCM 314 - Principles, Emergency, GI Tract and Hernias"),
            LibraryUnit(21, "GENERAL SURGERY II - BCM 322 - Hepatobiliary, Urology, Breast, Vascular and Specialty Surgery", "Clinical Medicine", "MBChB", "General Surgery II - BCM 322 - Hepatobiliary, Urology, Breast, Vascular and Specialty Surgery"),
            LibraryUnit(22, "Obstetrics and Gynaecology I - BCM 317", "Clinical Medicine", "MBChB", "Obstetrics and Gynaecology I - BCM 317"),
            LibraryUnit(23, "Obstetrics and Gynaecology II - BCM 323 - Pathology and Management", "Clinical Medicine", "MBChB", "Obstetrics and Gynaecology II - BCM 323 - Pathology and Management"),
            LibraryUnit(8, "General Pharmacology", "Clinical Medicine", "MBChB", "General Pharmacology"),
            LibraryUnit(9, "Clinical Pharmacology I: Autonomic, Cardiovascular, Respiratory, Gastrointestinal and Hematology", "Clinical Medicine", "MBChB", "Clinical Pharmacology I: Autonomic, Cardiovascular, Respiratory"),
            LibraryUnit(10, "Clinical Pharmacology II: Antimicrobials, CNS, Endocrine, Chemotherapy and Immunomodulators", "Clinical Medicine", "MBChB", "Clinical Pharmacology II: Antimicrobials, CNS, Endocrine"),
            LibraryUnit(29, "Clinical Pharmacology III - BCM 331 - Comprehensive and Applied Clinical Pharmacology", "Clinical Medicine", "MBChB", "Clinical Pharmacology III - BCM 331"),
            LibraryUnit(35, "Emergency Medicine and Life Support [ATLS & ACLS]", "Clinical Medicine", "MBChB", "Emergency Medicine and Life Support [ATLS & ACLS]"),
            LibraryUnit(36, "Child Health - BCM 312", "Clinical Medicine", "MBChB", "Child Health - BCM 312"),
            LibraryUnit(37, "Research Methodology - HRS 312", "Clinical Medicine", "MBChB", "Medical Research Methodology - HRS 312"),
            LibraryUnit(38, "RESEARCH METHODOLOGY", "Global Studies & Core Foundations", "Common Core Curriculum", "Research Methodology"),
            LibraryUnit(30, "INTRODUCTION TO PHILOSOPHY - EEN 114", "Global Studies & Core Foundations", "Common Core Curriculum", "Introduction to Philosophy - EEN 114"),
            LibraryUnit(31, "ENTREPRENEURSHIP - HSN 425", "Global Studies & Core Foundations", "Common Core Curriculum", "Entrepreneurship - HSN 425"),
            LibraryUnit(32, "BASIC COMPUTER SKILLS - BCM 111", "Global Studies & Core Foundations", "Common Core Curriculum", "Basic Computer Skills - BCM 111")
        )
    }

    val displayUnits = if (uiState.availableUnits.isNotEmpty()) uiState.availableUnits else fallbackUnits

    var searchQuery by remember { mutableStateOf("") }
    var selectedCategoryFilter by remember { mutableStateOf("All") }
    var addingUnitId by remember { mutableStateOf<Int?>(null) }

    val filteredUnits = remember(displayUnits, searchQuery, selectedCategoryFilter) {
        displayUnits.filter { unit ->
            val matchesSearch = searchQuery.isBlank() ||
                    unit.name.contains(searchQuery, ignoreCase = true) ||
                    unit.category.contains(searchQuery, ignoreCase = true) ||
                    unit.exactFieldName.contains(searchQuery, ignoreCase = true) ||
                    unit.exactCourseName.contains(searchQuery, ignoreCase = true) ||
                    unit.exactUnitGroupName.contains(searchQuery, ignoreCase = true)

            val matchesFilter = when (selectedCategoryFilter) {
                "All" -> true
                "Clinical Medicine" -> unit.exactFieldName.equals("Clinical Medicine", ignoreCase = true)
                "Global Studies & Core Foundations" -> unit.exactFieldName.equals("Global Studies & Core Foundations", ignoreCase = true)
                "MBChB" -> unit.exactCourseName.equals("MBChB", ignoreCase = true)
                "Common Core" -> unit.exactCourseName.contains("Common Core", ignoreCase = true)
                "Surgery" -> unit.name.contains("surgery", ignoreCase = true)
                "Pharmacology" -> unit.name.contains("pharmacology", ignoreCase = true)
                "Crash Courses" -> unit.name.contains("crash", ignoreCase = true)
                else -> true
            }

            matchesSearch && matchesFilter
        }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        DynamicBackground()

        Scaffold(
            containerColor = Color.Transparent,
            topBar = {
                TopAppBar(
                    title = {
                        Column {
                            Text("Add Unit to Syllabus", fontWeight = FontWeight.Black, fontSize = 20.sp)
                            Text(
                                text = "Authentic curriculum courses offered on Trace Backend",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.primary
                            )
                        }
                    },
                    navigationIcon = {
                        IconButton(onClick = onBack) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back")
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(
                        containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.5f)
                    )
                )
            }
        ) { padding ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
            ) {
                if (uiState.isLoading && addingUnitId == null) {
                    LinearProgressIndicator(modifier = Modifier.fillMaxWidth(), color = MaterialTheme.colorScheme.primary)
                }

                if (uiState.error != null) {
                    Text(
                        text = uiState.error!!,
                        color = MaterialTheme.colorScheme.error,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                        fontSize = 12.sp
                    )
                }

                if (uiState.successMessage != null) {
                    Surface(
                        color = Color(0xFF10B981).copy(alpha = 0.15f),
                        border = BorderStroke(1.dp, Color(0xFF10B981).copy(alpha = 0.4f)),
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(horizontal = 16.dp, vertical = 6.dp)
                    ) {
                        Row(modifier = Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.CheckCircle, contentDescription = null, tint = Color(0xFF10B981), modifier = Modifier.size(18.dp))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = uiState.successMessage!!,
                                color = Color(0xFF10B981),
                                fontWeight = FontWeight.Bold,
                                fontSize = 12.sp
                            )
                        }
                    }
                }

                // Search Bar
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    placeholder = { Text("Search 21+ backend units (e.g. Surgery, Pharmacology)...", fontSize = 12.sp) },
                    leadingIcon = { Icon(Icons.Default.Search, contentDescription = "Search", tint = MaterialTheme.colorScheme.primary) },
                    trailingIcon = {
                        if (searchQuery.isNotEmpty()) {
                            IconButton(onClick = { searchQuery = "" }) {
                                Icon(Icons.Default.Close, contentDescription = "Clear")
                            }
                        }
                    },
                    singleLine = true,
                    shape = RoundedCornerShape(16.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.7f),
                        unfocusedContainerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.7f)
                    )
                )

                // Category Filter Chips
                val filterChips = listOf("All", "Clinical Medicine", "Global Studies & Core Foundations", "MBChB", "Common Core", "Crash Courses", "Surgery", "Pharmacology")
                LazyRow(
                    contentPadding = PaddingValues(horizontal = 16.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                    modifier = Modifier.padding(bottom = 12.dp)
                ) {
                    items(filterChips) { chip ->
                        val isSelected = selectedCategoryFilter == chip
                        FilterChip(
                            selected = isSelected,
                            onClick = {
                                TactileFeedback.triggerSubtleClick(context)
                                selectedCategoryFilter = chip
                            },
                            label = { Text(chip, fontSize = 11.sp, fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal) },
                            colors = FilterChipDefaults.filterChipColors(
                                selectedContainerColor = MaterialTheme.colorScheme.primaryContainer,
                                selectedLabelColor = MaterialTheme.colorScheme.onPrimaryContainer
                            )
                        )
                    }
                }

                // Summary Row
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        "${filteredUnits.size} Units Available",
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary
                    )
                    Text(
                        "Synchronized with Trace Server",
                        fontSize = 10.sp,
                        color = MaterialTheme.colorScheme.outline
                    )
                }

                if (filteredUnits.isEmpty()) {
                    Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Icon(Icons.Default.MenuBook, contentDescription = null, tint = MaterialTheme.colorScheme.outline, modifier = Modifier.size(48.dp))
                            Spacer(modifier = Modifier.height(12.dp))
                            Text("No matching units found.", color = MaterialTheme.colorScheme.outline, fontSize = 13.sp)
                        }
                    }
                } else {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp)
                    ) {
                        val groupedByField = filteredUnits.groupBy { it.exactFieldName }
                        groupedByField.forEach { (fieldName, fieldUnits) ->
                            item {
                                Surface(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(top = 10.dp, bottom = 2.dp),
                                    shape = RoundedCornerShape(12.dp),
                                    color = MaterialTheme.colorScheme.primary.copy(alpha = 0.12f),
                                    border = BorderStroke(1.dp, MaterialTheme.colorScheme.primary.copy(alpha = 0.3f))
                                ) {
                                    Row(
                                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                                        verticalAlignment = Alignment.CenterVertically,
                                        horizontalArrangement = Arrangement.SpaceBetween
                                    ) {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            val fieldIcon = if (fieldName.contains("Medicine", ignoreCase = true)) Icons.Default.MedicalServices
                                            else if (fieldName.contains("Computer", ignoreCase = true)) Icons.Default.Computer
                                            else Icons.Default.Public
                                            Icon(fieldIcon, contentDescription = null, tint = MaterialTheme.colorScheme.primary, modifier = Modifier.size(16.dp))
                                            Spacer(modifier = Modifier.width(8.dp))
                                            Text(
                                                text = fieldName,
                                                fontWeight = FontWeight.Black,
                                                fontSize = 13.sp,
                                                color = MaterialTheme.colorScheme.primary
                                            )
                                        }
                                        Text(
                                            text = "${fieldUnits.size} Units Available",
                                            fontSize = 11.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = MaterialTheme.colorScheme.primary
                                        )
                                    }
                                }
                            }

                            val groupedByCourse = fieldUnits.groupBy { it.exactCourseName }
                            groupedByCourse.forEach { (courseName, courseUnits) ->
                                item {
                                    Text(
                                        text = "• Course: $courseName",
                                        fontSize = 12.sp,
                                        fontWeight = FontWeight.ExtraBold,
                                        color = MaterialTheme.colorScheme.secondary,
                                        modifier = Modifier.padding(start = 6.dp, top = 2.dp, bottom = 2.dp)
                                    )
                                }

                                items(courseUnits, key = { it.id }) { unit ->
                                    UnitBackendCard(
                                        unit = unit,
                                        isAdding = addingUnitId == unit.id,
                                        onAdd = {
                                            TactileFeedback.triggerSubtleClick(context)
                                            addingUnitId = unit.id
                                            viewModel.addUnit(unit.id, userId) {
                                                addingUnitId = null
                                                onUnitAdded()
                                            }
                                        }
                                    )
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun UnitBackendCard(
    unit: LibraryUnit,
    isAdding: Boolean,
    onAdd: () -> Unit
) {
    val isMedicine = unit.exactFieldName.contains("Medicine", ignoreCase = true)
    val categoryColor = if (isMedicine) Color(0xFF00E5FF) else Color(0xFF10B981)
    val categoryIcon: ImageVector = if (isMedicine) Icons.Default.MedicalServices else Icons.Default.Public

    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.85f)
        ),
        shape = RoundedCornerShape(16.dp),
        border = BorderStroke(1.dp, categoryColor.copy(alpha = 0.25f))
    ) {
        Row(
            modifier = Modifier.padding(14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Surface(
                shape = CircleShape,
                color = categoryColor.copy(alpha = 0.15f),
                modifier = Modifier.size(42.dp)
            ) {
                Box(contentAlignment = Alignment.Center) {
                    Icon(
                        imageVector = categoryIcon,
                        contentDescription = null,
                        tint = categoryColor,
                        modifier = Modifier.size(22.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = categoryColor.copy(alpha = 0.15f)
                    ) {
                        Text(
                            text = unit.exactFieldName.uppercase(),
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Black,
                            color = categoryColor,
                            modifier = Modifier.padding(horizontal = 5.dp, vertical = 2.dp)
                        )
                    }
                    Spacer(modifier = Modifier.width(6.dp))
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = MaterialTheme.colorScheme.surfaceVariant
                    ) {
                        Text(
                            text = unit.exactCourseName,
                            fontSize = 8.sp,
                            fontWeight = FontWeight.Bold,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            modifier = Modifier.padding(horizontal = 5.dp, vertical = 2.dp)
                        )
                    }
                    if (unit.name.contains("Crash Course", ignoreCase = true)) {
                        Spacer(modifier = Modifier.width(6.dp))
                        Surface(
                            shape = RoundedCornerShape(4.dp),
                            color = Color(0xFFF59E0B).copy(alpha = 0.15f)
                        ) {
                            Text(
                                text = "CRASH COURSE",
                                fontSize = 8.sp,
                                fontWeight = FontWeight.Black,
                                color = Color(0xFFF59E0B),
                                modifier = Modifier.padding(horizontal = 5.dp, vertical = 2.dp)
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = unit.name,
                    fontWeight = FontWeight.Bold,
                    fontSize = 13.sp,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
            }

            Spacer(modifier = Modifier.width(10.dp))

            Button(
                onClick = onAdd,
                enabled = !isAdding,
                shape = RoundedCornerShape(10.dp),
                contentPadding = PaddingValues(horizontal = 14.dp, vertical = 6.dp),
                modifier = Modifier.height(36.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = categoryColor.copy(alpha = 0.85f),
                    contentColor = Color.Black
                )
            ) {
                if (isAdding) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(14.dp),
                        strokeWidth = 2.dp,
                        color = Color.Black
                    )
                } else {
                    Icon(Icons.Default.Add, contentDescription = null, modifier = Modifier.size(15.dp))
                    Spacer(modifier = Modifier.width(4.dp))
                    Text("ADD", fontSize = 11.sp, fontWeight = FontWeight.ExtraBold)
                }
            }
        }
    }
}
