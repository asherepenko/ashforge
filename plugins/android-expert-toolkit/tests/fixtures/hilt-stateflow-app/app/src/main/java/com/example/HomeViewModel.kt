package com.example

@HiltViewModel
class HomeViewModel @Inject constructor(private val repo: HomeRepository) : ViewModel() {
    val state: StateFlow<Int> = MutableStateFlow(0)

    fun load() {
        GlobalScope.launch { repo.refresh() }
    }
}
