/// The IFBB Pro League Men's Open mandatory poses, in the Pro League's own
/// order.
///
/// Source and rationale: issue #4, "Men's Open mandatory poses: canonical
/// definitions, cues and checkpoints" - see `docs/research/mandatory-poses.md`.
/// The Pro League list is identical in NPC and NPC Worldwide. The international
/// IFBB rulebook lists only seven and omits Most Muscular entirely.
enum MandatoryPose {
  frontDoubleBiceps('Front Double Biceps'),
  frontLatSpread('Front Lat Spread'),
  sideChest('Side Chest'),
  backDoubleBiceps('Back Double Biceps'),
  backLatSpread('Back Lat Spread'),
  sideTriceps('Side Triceps'),
  abdominalsAndThighs('Abdominals and Thighs'),
  mostMuscular('Most Muscular');

  const MandatoryPose(this.displayName);

  /// The pose's name as the federation writes it. Shown to the athlete and
  /// spoken by the session timer.
  final String displayName;
}
