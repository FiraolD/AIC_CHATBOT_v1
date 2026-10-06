import React from 'react';
import { Phone, Mail, MapPin } from 'lucide-react';
import config from '../../config';

/** Slim footer with support contacts and an AI disclaimer. */
const Footer = () => (
  <footer className="border-t border-slate-200 bg-white pb-[env(safe-area-inset-bottom)]">
    <div className="mx-auto flex max-w-3xl flex-col items-center gap-1.5 px-4 py-3 text-center">
      <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs text-slate-500">
        <a
          href={`tel:${config.support.phone.replace(/[^+\d]/g, '')}`}
          className="flex items-center gap-1 hover:text-awash-700"
        >
          <Phone className="h-3 w-3" aria-hidden="true" />
          {config.support.phone}
        </a>
        <a
          href={`mailto:${config.support.email}`}
          className="flex items-center gap-1 hover:text-awash-700"
        >
          <Mail className="h-3 w-3" aria-hidden="true" />
          {config.support.email}
        </a>
        <span className="hidden items-center gap-1 sm:flex">
          <MapPin className="h-3 w-3" aria-hidden="true" />
          {config.support.address}
        </span>
      </div>
      <p className="text-[11px] text-slate-400">
        Answers are AI-generated. Please verify important details with smart Insurance.
      </p>
    </div>
  </footer>
);

export default Footer;
