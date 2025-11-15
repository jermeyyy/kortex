package com.example.kmp

import platform.Foundation.NSUserDefaults

/**
 * iOS-specific implementation of Repository.
 */
class IosRepository : Repository {
    
    private val userDefaults = NSUserDefaults.standardUserDefaults
    
    override suspend fun getData(): List<String> {
        val data = userDefaults.stringForKey("data") ?: ""
        return if (data.isEmpty()) emptyList() else data.split(",")
    }
    
    override suspend fun saveData(data: String): Boolean {
        return try {
            userDefaults.setObject(data, forKey = "data")
            true
        } catch (e: Exception) {
            false
        }
    }
}

/**
 * iOS-specific utility functions.
 */
object IosUtils {
    fun getDeviceInfo(): String {
        return "iOS Platform"
    }
}
