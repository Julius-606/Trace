package com.example.edu_ai.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "users")
data class UserEntity(
    @PrimaryKey val id: String,
    val username: String,
    val role: String,
    val sensoryMode: String,
    val semesterStatus: String,
    val aiPersona: String,
    val email: String? = null,
    val passwordHash: String? = null,
    val fullName: String? = null,
    val age: Int? = null,
    val coursePursued: String? = null,
    val referralCode: String? = null
)
