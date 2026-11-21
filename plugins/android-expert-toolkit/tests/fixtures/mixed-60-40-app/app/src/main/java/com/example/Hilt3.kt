package com.example

@HiltViewModel
class Hilt3 : ViewModel() {
    val state: StateFlow<Int> = MutableStateFlow(3)
}
