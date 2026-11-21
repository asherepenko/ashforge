package com.example

class App : Application() {
    override fun onCreate() {
        startKoin { modules(appModule) }
    }
}
