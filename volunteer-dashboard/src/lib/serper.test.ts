import { buildSearchQuery } from './serper';

describe('buildSearchQuery', () => {
  it('searches all platforms when no platform specified', () => {
    const q = buildSearchQuery({ location: 'Berlin' });
    expect(q).toContain('site:workaway.info');
    expect(q).toContain('site:worldpackers.com');
    expect(q).toContain('site:instagram.com');
    expect(q).toContain('site:volunteeryatra.com');
  });

  it('restricts to Workaway only when platform is Workaway', () => {
    const q = buildSearchQuery({ location: 'Berlin', platform: 'Workaway' });
    expect(q).toContain('site:workaway.info');
    expect(q).not.toContain('site:worldpackers.com');
    expect(q).not.toContain('site:instagram.com');
    expect(q).not.toContain('site:volunteeryatra.com');
  });

  it('restricts to Worldpackers only when platform is Worldpackers', () => {
    const q = buildSearchQuery({ location: 'Berlin', platform: 'Worldpackers' });
    expect(q).toContain('site:worldpackers.com');
    expect(q).not.toContain('site:workaway.info');
  });

  it('restricts to Instagram only when platform is Instagram', () => {
    const q = buildSearchQuery({ location: 'Berlin', platform: 'Instagram' });
    expect(q).toContain('site:instagram.com');
    expect(q).not.toContain('site:workaway.info');
  });

  it('restricts to VolunteerYatra only when platform is VolunteerYatra', () => {
    const q = buildSearchQuery({ location: 'Berlin', platform: 'VolunteerYatra' });
    expect(q).toContain('site:volunteeryatra.com');
    expect(q).not.toContain('site:workaway.info');
  });

  it('searches all platforms when platform is All', () => {
    const q = buildSearchQuery({ location: 'Berlin', platform: 'All' });
    expect(q).toContain('site:workaway.info');
    expect(q).toContain('site:worldpackers.com');
  });

  it('adds hostel keyword when hostelsOnly is true', () => {
    const q = buildSearchQuery({ location: 'Berlin', hostelsOnly: true });
    expect(q).toContain('hostel');
  });

  it('does not add hostel keyword when hostelsOnly is false', () => {
    const q = buildSearchQuery({ location: 'Berlin', hostelsOnly: false });
    expect(q).not.toContain('hostel');
  });

  it('combines platform filter with hostelsOnly', () => {
    const q = buildSearchQuery({ location: 'Berlin', platform: 'Worldpackers', hostelsOnly: true });
    expect(q).toContain('site:worldpackers.com');
    expect(q).not.toContain('site:workaway.info');
    expect(q).toContain('hostel');
  });

  it('includes category in query', () => {
    const q = buildSearchQuery({ location: 'Berlin', category: 'animals' });
    expect(q).toContain('animals');
  });
});
