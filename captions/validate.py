import xml.etree.ElementTree as ET

tree = ET.parse('../content/captions.fcpxml')
root = tree.getroot()

media = root.find('.//media')
print('Compound clip:', media.get('id'), media.get('name'))

effect = root.find('.//effect')
print('Effect UID:', effect.get('uid'))

ref_clip = root.find('.//event/ref-clip')
print('Event ref-clip ref:', ref_clip.get('ref'), 'name:', ref_clip.get('name'))

titles = list(root.iter('title'))
print('Title elements:', len(titles))

t = titles[0]
at = t.find('adjust-transform')
ts_defs = list(t.iter('text-style-def'))
print('First title: offset=%s dur=%s name=%s start=%s' % (
    t.get('offset'), t.get('duration'), t.get('name'), t.get('start')))
print('  adjust-transform position:', at.get('position') if at is not None else 'MISSING')
print('  text-style-defs:', len(ts_defs))
for d in ts_defs:
    ts = d.find('text-style')
    print('  [%s] fontColor=%s bg=%s' % (d.get('id'), ts.get('fontColor'), ts.get('backgroundColor')))

print('Caption elements (want 0):', len(list(root.iter('caption'))))
