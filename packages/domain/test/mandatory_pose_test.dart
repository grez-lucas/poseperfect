import 'package:poseperfect_domain/poseperfect_domain.dart';
import 'package:test/test.dart';

void main() {
  group('MandatoryPose', () {
    test('is the IFBB Pro League list, in the Pro League order', () {
      // Verbatim from the Pro League rulebook via issue #4, see
      // docs/research/mandatory-poses.md. Order is the least stable thing in
      // the sport - four distinct orderings appear across federations - so it
      // is pinned here rather than left to enum declaration order by accident.
      expect(MandatoryPose.values.map((p) => p.displayName).toList(), [
        'Front Double Biceps',
        'Front Lat Spread',
        'Side Chest',
        'Back Double Biceps',
        'Back Lat Spread',
        'Side Triceps',
        'Abdominals and Thighs',
        'Most Muscular',
      ]);
    });

    test('names both lat spreads as "Lat Spread", not "Rear Lat Spread"', () {
      // NPC uses both spellings inside a single document. #4 flagged the
      // inconsistency; we follow the Pro League list's own wording.
      expect(MandatoryPose.backLatSpread.displayName, 'Back Lat Spread');
      expect(MandatoryPose.frontLatSpread.displayName, 'Front Lat Spread');
    });
  });
}
