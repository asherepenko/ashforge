package com.example

interface HomeRepository {
    fun values(): Flow<Int>
    suspend fun refresh()
}
