package com.example

class UserRepositoryTest {
    val repository = mockk<UserRepository>()

    fun loads() {
        every { repository.get() } returns 1
        verify { repository.get() }
    }
}
