package com.example.kortex.sample

actual class Platform {
    actual val name: String = "Android"
}

actual fun getPlatform(): Platform = Platform()
