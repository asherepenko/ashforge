import Dependencies
struct NumberFactClient { var fetch: @Sendable (Int) async throws -> String }
extension NumberFactClient: DependencyKey { static let liveValue = NumberFactClient(fetch: { _ in "" }) }
