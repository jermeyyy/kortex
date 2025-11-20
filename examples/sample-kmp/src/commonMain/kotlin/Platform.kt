package com.example.kortex.sample

expect class Platform() {
    val name: String
}

expect fun getPlatform(): Platform
