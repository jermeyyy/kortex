package com.example.kortex.sample

// Mocking UIDevice for sample purposes as we don't have full iOS env here
class UIDevice {
    companion object {
        val currentDevice = UIDevice()
    }
    fun systemName(): String = "iOS"
    val systemVersion: String = "17.0"
}

actual class Platform {
    actual val name: String = UIDevice.currentDevice.systemName() + " " + UIDevice.currentDevice.systemVersion
}

actual fun getPlatform(): Platform = Platform()
