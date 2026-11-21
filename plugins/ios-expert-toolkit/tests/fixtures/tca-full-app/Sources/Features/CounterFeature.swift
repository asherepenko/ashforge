import ComposableArchitecture
@Reducer struct CounterFeature {
  @ObservableState struct State: Equatable {}
  enum Action {}
  @Dependency(\.numberFact) var numberFact
}
