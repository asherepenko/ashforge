package com.example

import dagger.Module
import dagger.Provides

@Module
class NetworkModule {
    @Provides
    fun provideClient(): Client = Client()
}
