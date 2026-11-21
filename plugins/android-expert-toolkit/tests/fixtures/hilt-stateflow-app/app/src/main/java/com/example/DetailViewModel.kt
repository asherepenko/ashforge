package com.example

@HiltViewModel
class DetailViewModel @Inject constructor(repo: HomeRepository) : ViewModel() {
    val state: StateFlow<Int> = repo.values().stateIn(viewModelScope, SharingStarted.Eagerly, 0)
}
