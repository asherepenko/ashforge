package com.example

import dagger.Module
import dagger.Provides

@Module
object DataModule {
    @Provides
    fun provideDb(): Db = Db()
}
