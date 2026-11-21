package com.example

import javax.inject.Inject

class MainActivity {
    @Inject lateinit var repository: UserRepository
}
