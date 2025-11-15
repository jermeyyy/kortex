package com.example.kmp

import android.content.Context
import android.content.SharedPreferences

/**
 * Android-specific implementation of Repository.
 */
class AndroidRepository(context: Context) : Repository {
    
    private val prefs: SharedPreferences = context.getSharedPreferences(
        "kmp_data",
        Context.MODE_PRIVATE
    )
    
    override suspend fun getData(): List<String> {
        val data = prefs.getString("data", "") ?: ""
        return if (data.isEmpty()) emptyList() else data.split(",")
    }
    
    override suspend fun saveData(data: String): Boolean {
        return try {
            prefs.edit()
                .putString("data", data)
                .apply()
            true
        } catch (e: Exception) {
            false
        }
    }
}

/**
 * Android-specific utility functions.
 */
object AndroidUtils {
    fun getDeviceInfo(): String {
        return "Android ${android.os.Build.VERSION.RELEASE}"
    }
}
