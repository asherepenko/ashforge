package com.example

import javax.inject.Inject

class UserRepository @Inject constructor(private val client: Client)
