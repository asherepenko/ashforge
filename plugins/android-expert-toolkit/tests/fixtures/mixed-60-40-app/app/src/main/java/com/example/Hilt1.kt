package com.example

@HiltViewModel
class Hilt1 : ViewModel() {
    val state: StateFlow<Int> = MutableStateFlow(1)
}
