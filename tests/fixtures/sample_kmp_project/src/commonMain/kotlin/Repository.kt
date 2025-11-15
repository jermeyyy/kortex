package com.example.kmp

/**
 * Repository interface for data access.
 * 
 * Common implementation across all platforms.
 */
interface Repository {
    suspend fun getData(): List<String>
    suspend fun saveData(data: String): Boolean
}

/**
 * Shared ViewModel for managing data.
 */
class SharedViewModel(private val repository: Repository) {
    
    private var cachedData: List<String>? = null
    
    suspend fun loadData(): List<String> {
        val data = repository.getData()
        cachedData = data
        return data
    }
    
    suspend fun addItem(item: String): Boolean {
        return repository.saveData(item)
    }
    
    fun getCachedData(): List<String>? = cachedData
}

/**
 * Utility class for common operations.
 */
object CommonUtils {
    fun formatMessage(message: String): String {
        return "KMP: $message"
    }
    
    fun isValidInput(input: String): Boolean {
        return input.isNotBlank() && input.length <= 1000
    }
}
