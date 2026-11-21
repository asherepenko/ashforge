package com.example

const val TEST_TOKEN = "abcdefghijklmnopqrstuvwxyz0123456789WXYZ"

class FakeHomeRepository : HomeRepository

class HomeViewModelTest {
    @Test
    fun loads() = runTest {
        flow.test { assertThat(awaitItem()).isEqualTo(0) }
    }
}
