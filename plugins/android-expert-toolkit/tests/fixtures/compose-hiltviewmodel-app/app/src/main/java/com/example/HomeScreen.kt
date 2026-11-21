package com.example

@Composable
fun HomeScreen(viewModel: HomeViewModel = hiltViewModel()) {
    val other = viewModel<OtherViewModel>()
}
