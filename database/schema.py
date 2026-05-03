"""Esquema físico base de la V2 con SQLAlchemy 2.0."""

from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from database.connection import engine


class Base(DeclarativeBase):
    """Base declarativa del proyecto."""


class Lavanderia(Base):
    __tablename__ = "lavanderias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_local: Mapped[str] = mapped_column(String(150), nullable=False)
    nombre_responsable: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    telefono: Mapped[Optional[str]] = mapped_column(String(50))
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Rol(Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("lavanderia_id", "nombre", name="uq_roles_lavanderia_nombre"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    lavanderia_id: Mapped[int] = mapped_column(
        ForeignKey("lavanderias.id", ondelete="CASCADE"),
        nullable=False,
    )


class Permiso(Base):
    __tablename__ = "permisos"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255))
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class RolPermiso(Base):
    __tablename__ = "roles_permisos"
    __table_args__ = (
        UniqueConstraint("rol_id", "permiso_id", name="uq_roles_permisos"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    rol_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    permiso_id: Mapped[int] = mapped_column(
        ForeignKey("permisos.id", ondelete="CASCADE"),
        nullable=False,
    )


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint(
            "lavanderia_id",
            "nombre_usuario",
            name="uq_usuarios_lavanderia_nombre_usuario",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_usuario: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    lavanderia_id: Mapped[int] = mapped_column(
        ForeignKey("lavanderias.id", ondelete="CASCADE"),
        nullable=False,
    )
    rol_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
    )


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("lavanderia_id", "ruc_ci", name="uq_clientes_lavanderia_ruc_ci"),
        CheckConstraint(
            "tipo_cliente IN ('particular', 'empresa', 'generico')",
            name="ck_clientes_tipo_cliente",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo_cliente: Mapped[str] = mapped_column(String(20), nullable=False)
    ruc_ci: Mapped[Optional[str]] = mapped_column(String(50))
    telefono: Mapped[Optional[str]] = mapped_column(String(50))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    lavanderia_id: Mapped[int] = mapped_column(
        ForeignKey("lavanderias.id", ondelete="CASCADE"),
        nullable=False,
    )


class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = (
        UniqueConstraint(
            "lavanderia_id",
            "nombre_producto",
            name="uq_productos_lavanderia_nombre_producto",
        ),
        CheckConstraint("precio >= 0", name="ck_productos_precio_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_producto: Mapped[str] = mapped_column(String(150), nullable=False)
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    lavanderia_id: Mapped[int] = mapped_column(
        ForeignKey("lavanderias.id", ondelete="CASCADE"),
        nullable=False,
    )


class TipoVehiculo(Base):
    __tablename__ = "tipos_vehiculo"
    __table_args__ = (
        UniqueConstraint(
            "lavanderia_id",
            "nombre",
            name="uq_tipos_vehiculo_lavanderia_nombre",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    lavanderia_id: Mapped[int] = mapped_column(
        ForeignKey("lavanderias.id", ondelete="CASCADE"),
        nullable=False,
    )


class Vehiculo(Base):
    __tablename__ = "vehiculos"
    __table_args__ = (
        UniqueConstraint(
            "lavanderia_id",
            "matricula",
            name="uq_vehiculos_lavanderia_matricula",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    matricula: Mapped[Optional[str]] = mapped_column(String(20))
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    lavanderia_id: Mapped[int] = mapped_column(
        ForeignKey("lavanderias.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo_vehiculo_id: Mapped[int] = mapped_column(
        ForeignKey("tipos_vehiculo.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cliente_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("clientes.id", ondelete="SET NULL"),
    )


class Servicio(Base):
    __tablename__ = "servicios"
    __table_args__ = (
        UniqueConstraint(
            "lavanderia_id",
            "nombre_servicio",
            name="uq_servicios_lavanderia_nombre_servicio",
        ),
        CheckConstraint("precio >= 0", name="ck_servicios_precio_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_servicio: Mapped[str] = mapped_column(String(150), nullable=False)
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    lavanderia_id: Mapped[int] = mapped_column(
        ForeignKey("lavanderias.id", ondelete="CASCADE"),
        nullable=False,
    )


class Venta(Base):
    __tablename__ = "ventas"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_ventas_total_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha_venta: Mapped["date"] = mapped_column(Date, nullable=False)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    tipo_cobro: Mapped[str] = mapped_column(String(50), nullable=False)
    metodo_pago: Mapped[Optional[str]] = mapped_column(String(50))
    requiere_factura: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    observacion: Mapped[Optional[str]] = mapped_column(Text)
    cliente_id: Mapped[int] = mapped_column(
        ForeignKey("clientes.id", ondelete="RESTRICT"),
        nullable=False,
    )
    lavanderia_id: Mapped[int] = mapped_column(
        ForeignKey("lavanderias.id", ondelete="CASCADE"),
        nullable=False,
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )
    vehiculo_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("vehiculos.id", ondelete="SET NULL"),
    )


class DetalleVenta(Base):
    __tablename__ = "detalles_venta"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_detalles_venta_cantidad_positiva"),
        CheckConstraint(
            "precio_unitario >= 0",
            name="ck_detalles_venta_precio_unitario_no_negativo",
        ),
        CheckConstraint("subtotal >= 0", name="ck_detalles_venta_subtotal_no_negativo"),
        CheckConstraint(
            "(servicio_id IS NOT NULL AND producto_id IS NULL) "
            "OR (servicio_id IS NULL AND producto_id IS NOT NULL)",
            name="ck_detalles_venta_servicio_xor_producto",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    cantidad: Mapped[int] = mapped_column(nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    venta_id: Mapped[int] = mapped_column(
        ForeignKey("ventas.id", ondelete="CASCADE"),
        nullable=False,
    )
    servicio_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("servicios.id", ondelete="RESTRICT"),
    )
    producto_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("productos.id", ondelete="RESTRICT"),
    )


class CategoriaEgreso(Base):
    __tablename__ = "categorias_egreso"
    __table_args__ = (
        UniqueConstraint(
            "lavanderia_id",
            "nombre_categoria",
            name="uq_categorias_egreso_lavanderia_nombre_categoria",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_categoria: Mapped[str] = mapped_column(String(150), nullable=False)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    lavanderia_id: Mapped[int] = mapped_column(
        ForeignKey("lavanderias.id", ondelete="CASCADE"),
        nullable=False,
    )


class Egreso(Base):
    __tablename__ = "egresos"
    __table_args__ = (
        CheckConstraint("monto >= 0", name="ck_egresos_monto_no_negativo"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    fecha: Mapped["date"] = mapped_column(Date, nullable=False)
    created_at: Mapped["datetime"] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    estado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    lavanderia_id: Mapped[int] = mapped_column(
        ForeignKey("lavanderias.id", ondelete="CASCADE"),
        nullable=False,
    )
    categoria_egreso_id: Mapped[int] = mapped_column(
        ForeignKey("categorias_egreso.id", ondelete="RESTRICT"),
        nullable=False,
    )
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
    )


Index("ix_ventas_lavanderia_fecha", Venta.lavanderia_id, Venta.fecha_venta)
Index("ix_egresos_lavanderia_fecha", Egreso.lavanderia_id, Egreso.fecha)
Index("ix_detalles_venta_venta_id", DetalleVenta.venta_id)


def create_tables():
    """Crea todas las tablas base del modelo V2."""
    Base.metadata.create_all(bind=engine)
