// Every internal link goes through url() so the site works both at the domain
// root and under a GitHub Pages project path such as /devstack/.
const base = import.meta.env.BASE_URL.replace(/\/$/, '');

export function url(path = '/'): string {
  const clean = path.startsWith('/') ? path : `/${path}`;
  return `${base}${clean}`;
}

export function isCurrent(pathname: string, href: string): boolean {
  const target = url(href).split('#')[0];
  if (target === url('/')) return pathname === target;
  return pathname.startsWith(target);
}
