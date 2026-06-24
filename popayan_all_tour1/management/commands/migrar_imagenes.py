from django.core.management.base import BaseCommand
from popayan_all_tour1.models import Hotel, Restaurante, Museos, Iglesias
import cloudinary.uploader
import os


class Command(BaseCommand):
    help = 'Migra imágenes locales a Cloudinary'

    def handle(self, *args, **kwargs):
        modelos = [
            ('Hoteles', Hotel),
            ('Restaurantes', Restaurante),
            ('Museos', Museos),
            ('Iglesias', Iglesias),
        ]
        
        total_migrados = 0
        total_errores = 0
        
        for nombre, Modelo in modelos:
            self.stdout.write(f'\n{"="*60}')
            self.stdout.write(f'🔄 Migrando {nombre}...')
            self.stdout.write(f'{"="*60}\n')
            
            # Solo objetos con imagen local y sin URL de Cloudinary
            objetos = Modelo.objects.filter(
                imagen__isnull=False
            ).exclude(imagen='').filter(imagen_url__isnull=True)
            
            total = objetos.count()
            self.stdout.write(f'📊 Total a migrar: {total}\n')
            
            for idx, obj in enumerate(objetos, 1):
                try:
                    # Verificar que el archivo existe
                    if not os.path.exists(obj.imagen.path):
                        self.stdout.write(f'⚠️  [{idx}/{total}] {obj.nombre} - Archivo no encontrado')
                        continue
                    
                    # Subir a Cloudinary
                    self.stdout.write(f'⏳ [{idx}/{total}] Subiendo {obj.nombre}...')
                    
                    resultado = cloudinary.uploader.upload(
                        obj.imagen.path,
                        folder=f"popayan/{nombre.lower()}",
                        public_id=f"{obj.id}_{obj.nombre[:30].replace(' ', '_')}",
                        overwrite=True,
                        resource_type="image"
                    )
                    
                    # Guardar la URL
                    obj.imagen_url = resultado['secure_url']
                    obj.save(update_fields=['imagen_url'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ [{idx}/{total}] {obj.nombre}\n'
                            f'   URL: {resultado["secure_url"][:80]}...\n'
                        )
                    )
                    total_migrados += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ [{idx}/{total}] Error en {obj.nombre}: {str(e)}\n'
                        )
                    )
                    total_errores += 1
            
            self.stdout.write(f'\n✅ {nombre} completado\n')
        
        # Resumen final
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.SUCCESS(f'🎉 MIGRACIÓN COMPLETADA'))
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'✅ Total migrados: {total_migrados}')
        self.stdout.write(f'❌ Total errores: {total_errores}')
        self.stdout.write(f'{"="*60}\n')