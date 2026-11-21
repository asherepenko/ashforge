package com.example

@HiltViewModel
class Hilt2 : ViewModel() {
    val state: StateFlow<Int> = MutableStateFlow(2)
}
