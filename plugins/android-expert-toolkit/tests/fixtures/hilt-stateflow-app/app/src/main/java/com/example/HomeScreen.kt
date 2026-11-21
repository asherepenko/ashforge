package com.example

@Composable
fun HomeScreen(items: List<String>) {
    Icon(Icons.Default.Add, null)
    Image(painterResource(R.drawable.logo), null)
    LazyColumn { items(items) { Text(it) } }
    Box(Modifier.semantics { }.clickable { })
}
