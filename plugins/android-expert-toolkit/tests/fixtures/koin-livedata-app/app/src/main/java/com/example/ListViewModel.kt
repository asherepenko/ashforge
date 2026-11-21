package com.example

class ListViewModel : ViewModel() {
    val items = MutableLiveData<List<String>>()
}
