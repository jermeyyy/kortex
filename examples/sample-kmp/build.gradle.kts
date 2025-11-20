plugins {
    kotlin("multiplatform") version "1.9.20"
    id("com.android.library")
}

kotlin {
    androidTarget()
    iosX64()
    iosArm64()
    iosSimulatorArm64()

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:1.7.3")
            }
        }
        val androidMain by getting
        val iosMain by getting
    }
}

android {
    namespace = "com.example.kortex.sample"
    compileSdk = 34
}
