import { afterEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, mount } from '@vue/test-utils';
import RegisterView from './RegisterView.vue';

const states = [
  { id: 1, name: 'Aguascalientes' },
  { id: 2, name: 'Oaxaca' },
];

const catalogs = [
  '/api/catalogs/genders',
  '/api/catalogs/age-ranges',
  '/api/catalogs/occupations',
  '/api/catalogs/sectors',
  '/api/catalogs/yes-no',
  '/api/catalogs/education-levels',
];

describe('municipios en el registro', () => {
  afterEach(() => {
    localStorage.clear();
    vi.unstubAllGlobals();
  });

  it('carga municipios del estado seleccionado y limpia la selección al cambiar de estado', async () => {
    const requests: string[] = [];
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      requests.push(url);

      if (url === '/api/catalogs/states') {
        return new Response(JSON.stringify(states), { status: 200 });
      }

      if (url === '/api/catalogs/municipalities?state_id=2') {
        return new Response(JSON.stringify([
          { id: 10, state_id: 2, code: '20208', name: 'San Juan Mixtepec', is_other: false },
          { id: 11, state_id: 2, code: '20209', name: 'San Juan Mixtepec', is_other: false },
        ]), { status: 200 });
      }

      if (url === '/api/catalogs/municipalities?state_id=1') {
        return new Response(JSON.stringify([
          { id: 20, state_id: 1, name: 'Aguascalientes', is_other: false },
        ]), { status: 200 });
      }

      if (catalogs.includes(url)) {
        return new Response(JSON.stringify([{ id: 1, name: 'Opción' }]), { status: 200 });
      }

      throw new Error(`Unexpected request: ${url}`);
    }));

    const wrapper = mount(RegisterView);
    await flushPromises();

    const field = (name: string) => wrapper.findAll('label').find((label) =>
      label.find('span').text().trim() === name
    )!;
    const input = (name: string) => field(name).find('input');
    const continueButton = () => wrapper.findAll('button').find((button) =>
      button.text().trim() === 'Continuar'
    )!;

    await input('Nombre(s)').setValue('Ana');
    await input('Apellido paterno').setValue('López');
    await input('Apellido materno').setValue('García');
    await input('CURP').setValue('AAAA000000AAAAAA00');
    await continueButton().trigger('click');
    await flushPromises();

    await input('Correo electrónico personal').setValue('ana@example.com');
    await input('Contraseña').setValue('password123');
    await input('Confirmar contraseña').setValue('password123');
    await continueButton().trigger('click');
    await flushPromises();

    const stateSelect = field('Estado').find('select');
    let municipalitySelect = field('Municipio').find('select');

    expect(municipalitySelect.element.disabled).toBe(true);

    await stateSelect.setValue('2');
    await flushPromises();
    municipalitySelect = field('Municipio').find('select');

    expect(requests).toContain('/api/catalogs/municipalities?state_id=2');
    expect(municipalitySelect.findAll('option').map(option => option.text())).toEqual([
      'Selecciona tu municipio',
      'San Juan Mixtepec (clave 20208)',
      'San Juan Mixtepec (clave 20209)',
    ]);

    await municipalitySelect.setValue('10');
    await stateSelect.setValue('1');
    await flushPromises();
    municipalitySelect = field('Municipio').find('select');

    expect(requests).toContain('/api/catalogs/municipalities?state_id=1');
    expect(municipalitySelect.element.selectedIndex).toBe(0);
    expect(municipalitySelect.findAll('option').map(option => option.text())).toEqual([
      'Selecciona tu municipio',
      'Aguascalientes',
    ]);

    wrapper.unmount();
  });

  it('no permite avanzar si faltan datos personales', async () => {
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === '/api/catalogs/states' || catalogs.includes(url)) {
        return new Response(JSON.stringify(url === '/api/catalogs/states' ? states : [{ id: 1, name: 'Opción' }]), { status: 200 });
      }
      throw new Error(`Unexpected request: ${url}`);
    }));

    const wrapper = mount(RegisterView);
    await flushPromises();

    const continueButton = wrapper.findAll('button').find((button) =>
      button.text().trim() === 'Continuar'
    )!;
    await continueButton.trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('Completa tu nombre y apellidos.');
    expect(wrapper.text()).toContain('Paso 1 de 4');

    wrapper.unmount();
  });
});
